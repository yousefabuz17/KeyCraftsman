import base64
import json
import math
import operator
import re
import sys
import textwrap
from collections import namedtuple
from concurrent.futures import as_completed, ThreadPoolExecutor
from itertools import cycle, islice
from functools import cache, cached_property, partial
from pathlib import Path
from secrets import SystemRandom
from string import (
    ascii_letters,
    ascii_lowercase,
    ascii_uppercase,
    digits,
    hexdigits,
    octdigits,
    punctuation,
    whitespace,
)
from typing import Any, Iterable, NamedTuple, Union


class KeyException(BaseException):
    """
    A custom exception class derived from `BaseException` for managing errors associated with generating or exporting key(s).
    This exception should be raised when encountering issues in the process of generating or exporting keys within the application.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class KeyCraftsman:
    """
    `KeyCraftsman` is a Python class designed to generate secure and customizable keys.
    It offers features such as specifying key length, excluding characters, including all characters,
    URL-safe encoding, and more. The generated key can be exported to a file with optional formatting.

    #### Features:
        - `Key Generation`: Generate secure and customizable keys with various parameters.
        - `Key Length`: Specify the length of the generated keys.
        - `Exclude Characters`: Exclude specific characters from the generated keys.
        - `Include All Characters`: Include all ASCII letters, digits, and punctuation in the generated keys.
        - `URL-Safe Encoding`: Utilize URL-safe base64 encoding for generated keys.
        - `Export Key(s)`: Export the generated key(s) to a file with optional formatting.
            - File will be created in the current working directory.
        - `Custom Text Wrapping`: Wrap the generated key with an initial header and custom separators.
        - `Multiple Key Generation`: Generate multiple keys with a single instance.
        - `Custom Key File Name`: Specify a custom name for the exported key file.
        - `Overwrite Key File`: Overwrite the key file if it already exists.

    #### Parameters:
        - `key_length` (int): The length of the generated key. Defaults to 32.
            - The key length must be a positive integer.
            - The maximum capacity is determined by the system's maximum integer size.
        - `exclude_chars` (str): Characters to exclude from the generated key.
            - If not specified, no characters will be excluded.
            - Use the `return_chart` parameter from `char_excluder()` to view all possible exclude types.
            - Whitespace characters are automatically excluded from the charset.
            - Examples:
                - `exclude_chars="punct"` will exclude punctuation characters from the generated key.
                - `exclude_chars="octo_ascii_upper_punct"` will exclude octal digits, uppercase ASCII letters, and punctuation characters.
        - `include_all_chars` (bool): Whether to include all characters (ASCII letters, digits, and punctuation).
        - `urlsafe_encoding` (bool): Whether to use URL-safe base64 encoding. Defaults to False.
            - If True, the generated key will be encoded using URL-safe base64 encoding.
            - `Fernet Compatibility`:
                - URL-safe encoding with a length of 32 works seamlessly for Fernet encryption.
                - URL-safe encoding is recommended for Fernet encryption with a key length of 32.
        - `num_of_keys` (int): Number of keys to generate when using `export_keys()`.
            - If not specified, the default number of keys is 2.
            - The maximum number of keys is determined by the system's maximum integer size.
        - `key_header` (str): Initial header for the generated key.
        - `sep` (str): The specified separator for text wrapping.
            - If not specified, the key will not be wrapped with a separator.
            - It is recommended to use one character of any standard characters for the separator (e.g., ascii_letters, digits).
        - `sep_width` (int): Width for text wrapping when using separators.
            - If not specified, the default width is 1 less than the specified key length.
            - The width must be 1 less than the key length to prevent the separator from being excluded.
            - The separator will be excluded if the width is equal to or greater than the key length.
            - The width is only applicable when using separators.
        - `keyfile_name` (str): Name of the file when exporting key(s).
            - If not specified, a default file name will be used.
            - The default file name is 'generated_key' for single keys and 'generated_keys' for multiple keys.
        - `overwrite_keyfile` (bool): Whether to overwrite the key file if it already exists.
            - If False, a unique file name will be generated to avoid overwriting the existing file.
            - If True, the existing file will be overwritten with the new key(s).

    #### Raises:
        - `NotImplementedError`: When combining URL-safe encoding with custom text wrapping separators.
        - `KeyException`: When specifying both 'exclude_chars' and 'include_all_chars' parameters.

    #### Attributes:
        - `key`: Cached property to retrieve a single generated key.
        - `keys`: Cached property to retrieve a dictionary of multiple generated keys.
        - `_EXECUTOR`: Class attribute for the ThreadPoolExecutor.
        - `_ALL_CHARS`: Class attribute containing all ASCII letters, digits, and punctuation.
        - `_MIN_CAPACITY`: Class attribute defining the minimum key capacity.
        - `_MAX_CAPACITY`: Class attribute defining the maximum key capacity.

    #### Methods:
        - `export_key`(): Exports the generated key to a file.
        - `export_keys`(): Exports multiple generated keys to a JSON file.

    #### Example:
        ```python
        key_gen = KeyCraftsman(key_length=32, num_of_keys=2, include_all_chars=False, urlsafe_encoding=True)

        key = key_gen.key # Retrieve a single generated key.
        # Output: b'...'

        keys = key_gen.keys # Retrieve a dictionary of multiple generated keys.
        # Output: {'key-1': b'...', 'key-2': b'...'}

        key_gen.export_key() # Export the generated key to a file.
        # Output: 'generated_key.bin has successfully been exported.'

        key_gen.export_keys() # Export multiple generated keys to a JSON file.
        # Output: 'generated_keys.json has successfully been exported.'
        ```
    """

    _EXECUTOR = ThreadPoolExecutor
    _ALL_CHARS: str = ascii_letters + digits + punctuation
    _MIN_CAPACITY: int = int(1e6)
    _MAX_CAPACITY: int = sys.maxsize

    def __init__(
        self,
        key_length: int = 32,
        exclude_chars: str = "",
        include_all_chars: bool = False,
        urlsafe_encoding: bool = False,
        num_of_keys: int = None,
        key_header: str = "",
        sep: str = "",
        sep_width: int = None,
        keyfile_name: str = "",
        overwrite_keyfile: bool = False,
    ) -> None:
        self._key_length = key_length
        self._exclude_chars = exclude_chars
        self._include_all = include_all_chars
        self._urlsafe = urlsafe_encoding
        self._num_of_keys = num_of_keys
        self._key_header = key_header
        self._sep = sep
        self._width = sep_width
        self._kfile_name = keyfile_name
        self._overwrite = overwrite_keyfile
        self._key = None
        self._keys = None

        if all((self._urlsafe, any((self._sep, self._width, self._key_header)))):
            raise NotImplementedError(
                f"\nCombining URL-safe encoding with custom text wrapping separators is not supported in this version (v{__version__}). "
                "\nPlease choose either URL-safe encoding or custom separators, but not both."
            )

        if all((self._exclude_chars, self._include_all)):
            raise KeyException(
                "Cannot specify both 'exclude_chars' and 'include_all_chars' parameters."
            )

    @staticmethod
    def _compiler(
        defaults: Iterable,
        k: str,
        escape_default: bool = True,
        escape_k: bool = True,
        search: bool = True,
    ) -> re.Match:
        valid_instances = (int, str, bool, bytes, Iterable)
        if any((not k, not isinstance(k, valid_instances), hasattr(k, "__str__"))):
            esc_k = str(k)
        else:
            raise KeyException(
                f"The value for 'k' is not a valid type."
                f"\nk value and type: ({k =}, {type(k) =})"
            )

        defaults_ = map(re.escape, map(str, defaults))
        flag = "|" if escape_default else ""
        pattern = f"{flag}".join(defaults_)
        if escape_k:
            esc_k = "|".join(map(re.escape, k))

        compiler = re.compile(pattern, re.IGNORECASE)
        if not search:
            compiled = compiler.match(esc_k)
        else:
            compiled = compiler.search(esc_k)
        return compiled

    @staticmethod
    def _base64_key(key: str, base_type="encode") -> bytes:
        base = [base64.urlsafe_b64decode, base64.urlsafe_b64encode][
            base_type == "encode"
        ]
        try:
            return base(key)
        except Exception as e_error:
            raise KeyException(
                f"An error occurred during base64 {'encoding' if base_type == 'encode' else 'decoding'}:"
                f"\n{e_error}"
            )

    @staticmethod
    def _filter_chars(s: str, *, exclude_chars: str = "") -> str:
        """
        Filter characters in the given string, excluding those specified.

        #### Parameters:
            - `s` (str): The input string to be filtered.
            - `exclude_chars` (str): Characters to be excluded from the filtering process.

        #### Returns:
            - `str`: The filtered string with specified characters exclude_charsd.

        #### Notes:
            - This method employs the `translate` method to efficiently filter characters.
            - To exclude additional characters, provide them as a string in the `exclude_chars` parameter.
        """
        return "".join(s).translate(str.maketrans("", "", whitespace + exclude_chars))

    @classmethod
    def _whitespace_checker(cls, key) -> None:
        if key == "whitespace" or cls._compiler(key, whitespace):
            print(
                KeyException(
                    f"{whitespace = !r} is already excluded from the charset.\n"
                )
            )

    @classmethod
    def char_excluder(
        cls, key: str = "punct", return_chart: bool = False
    ) -> Union[dict[str, str], str, None]:
        """
        Exclude specific character sets based on the provided key.

        #### Parameters:
            - key (str): The key to select the character set to exclude_chars.
            - return_chart (bool): If True, returns the dicitonary containing all possible exluce types.

        #### Returns:
            - str: The selected character set based on the key to be excluded from the generated passkey.

        #### Possible values for key:
            - 'punct': exclude_charss punctuation characters.
            - 'ascii': exclude_charss ASCII letters (both uppercase and lowercase).
            - 'ascii_lower': exclude_charss lowercase ASCII letters.
            - 'ascii_upper': exclude_charss uppercase ASCII letters.
            - 'ascii_punct': exclude_charss both ASCII letters and punctuation characters.
            - 'ascii_lower_punct': exclude_charss both lowercase ASCII letters and punctuation characters.
            - 'ascii_upper_punct': exclude_charss both uppercase ASCII letters and punctuation characters.
            - 'digits': exclude_charss digits (0-9).
            - 'digits_ascii': exclude_charss both digits and ASCII letters.
            - 'digits_punct': exclude_charss both digits and punctuation characters.
            - 'digits_ascii_lower': exclude_charss both digits and lowercase ASCII letters.
            - 'digits_ascii_upper': exclude_charss both digits and uppercase ASCII letters.
            - 'digits_ascii_lower_punct': exclude_charss digits, lowercase ASCII letters, and punctuation characters.
            - 'digits_ascii_upper_punct': exclude_charss digits, uppercase ASCII letters, and punctuation characters.
            - 'hexdigits': exclude_charss hexadecimal digits (0-9, a-f, A-F).
            - 'hex_punct': exclude_charss hexadecimal digits and punctuation characters.
            - 'hex_ascii': exclude_charss hexadecimal digits and ASCII letters.
            - 'hex_ascii_lower': exclude_charss hexadecimal digits and lowercase ASCII letters.
            - 'hex_ascii_upper': exclude_charss hexadecimal digits and uppercase ASCII letters.
            - 'hex_ascii_punct': exclude_charss hexadecimal digits, ASCII letters, and punctuation characters.
            - 'hex_ascii_lower_punct': exclude_charss hexadecimal digits, lowercase ASCII letters, and punctuation characters.
            - 'hex_ascii_upper_punct': exclude_charss hexadecimal digits, uppercase ASCII letters, and punctuation characters.
            - 'octodigits': exclude_charss octal digits (0-7).
            - 'octo_punct': exclude_charss octal digits and punctuation characters.
            - 'octo_ascii': exclude_charss octal digits and ASCII letters.
            - 'octo_ascii_lower': exclude_charss octal digits and lowercase ASCII letters.
            - 'octo_ascii_upper': exclude_charss octal digits and uppercase ASCII letters.
            - 'octo_ascii_punct': exclude_charss octal digits, ASCII letters, and punctuation characters.
            - 'octo_ascii_lower_punct': exclude_charss octal digits, lowercase ASCII letters, and punctuation characters.
            - 'octo_ascii_upper_punct': exclude_charss octal digits, uppercase ASCII letters, and punctuation characters.

        """
        cls._obj_instance(key, obj_type=str)
        cls._whitespace_checker(key)

        all_chars = {
            "punct": punctuation,
            "ascii": ascii_letters,
            "ascii_lower": ascii_lowercase,
            "ascii_upper": ascii_uppercase,
            "ascii_punct": ascii_letters + punctuation,
            "ascii_lower_punct": ascii_lowercase + punctuation,
            "ascii_upper_punct": ascii_uppercase + punctuation,
            "digits": digits,
            "digits_ascii": digits + ascii_letters,
            "digits_punct": digits + punctuation,
            "digits_ascii_lower": digits + ascii_lowercase,
            "digits_ascii_upper": digits + ascii_uppercase,
            "digits_ascii_lower_punct": digits + ascii_lowercase + punctuation,
            "digits_ascii_upper_punct": digits + ascii_uppercase + punctuation,
            "hexdigits": hexdigits,
            "hex_punct": hexdigits + punctuation,
            "hex_ascii": hexdigits + ascii_letters,
            "hex_ascii_lower": hexdigits + ascii_lowercase,
            "hex_ascii_upper": hexdigits + ascii_uppercase,
            "hex_ascii_lower_punct": hexdigits + ascii_lowercase + punctuation,
            "hex_ascii_upper_punct": hexdigits + ascii_uppercase + punctuation,
            "octdigits": octdigits,
            "oct_punct": octdigits + punctuation,
            "oct_ascii": octdigits + ascii_letters,
            "oct_ascii_lower": octdigits + ascii_lowercase,
            "oct_ascii_upper": octdigits + ascii_uppercase,
            "oct_ascii_punct": octdigits + ascii_letters + punctuation,
            "oct_ascii_lower_punct": octdigits + ascii_lowercase + punctuation,
            "oct_ascii_upper_punct": octdigits + ascii_uppercase + punctuation,
        }
        if return_chart:
            return all_chars
        return all_chars.get(key)

    @classmethod
    def _sig_larger(cls, *args) -> NamedTuple:
        """
        Calculate the significant difference between two numerical values.

        - Special Note:
            - The 'status' field indicates whether the absolute difference between the provided values
            is within the threshold (1e6). If 'status' is False, the 'threshold' field will be the maximum
            of the provided values and the threshold.
        """

        if len(args) == 2:
            threshold = cls._MIN_CAPACITY
            Sig = namedtuple("SigLarger", ("status", "threshold"))
            abs_diff = abs(operator.sub(*args))
            status: bool = operator.le(*map(math.log1p, (abs_diff, threshold)))
            return Sig(status, max(max(args), threshold))
        raise KeyException(
            f"Excessive arguments provided; requires precisely two numerical values, such as {int} or {float}."
        )

    def _check_scale(self, length) -> int:
        if length >= self._MIN_CAPACITY:
            return self._MAX_CAPACITY - 1
        elif self._sig_larger(length, self._MIN_CAPACITY).status:
            return length
        return self._MIN_CAPACITY

    @classmethod
    def _length_checker(cls, length) -> int:
        if any((not length, not isinstance(length, int))):
            raise KeyException("The key length must be a positive integer.")

        elif length >= (max_length := cls._MAX_CAPACITY):
            raise KeyException(
                f"Key length exceeds the maximum allowed capacity of {max_length = !r} characters. "
                f"Received key with {length = !r}."
            )
        return length

    @staticmethod
    def _obj_instance(obj: Any, obj_type: Any = str) -> Any:
        if not isinstance(obj, obj_type):
            raise KeyException(
                f"The provided value must be of type {obj_type}."
                f"\nProvided value {obj = !r} ({type(obj)!r})"
            )
        return obj

    def _wrap_text(self, text: str) -> str:
        """
        Wrap text with a specified separator is not implemented in this program.

        This program currently does not support the usage of special characters as separators
        when wrapping text. If you require custom separators, please refrain from using
        special characters, and consider using standard characters with separators.
        """
        if self._compiler(text, punctuation):
            print(
                NotImplementedError(
                    "\n[SPECIAL CHARACTERS DETECTED]\n"
                    "This program is primarily designed to support separators with standard characters only. "
                    "To avoid potential issues, refrain from using separators with special characters. "
                    "If seperators required, consider using standard characters such as ascii_letters and digits (default)."
                    "\n"
                )
            )
        self._obj_instance(self._sep)
        self._obj_instance(self._key_header)
        self._width = (
            1 if not self._width else self._obj_instance(self._width, obj_type=int)
        )

        # Excludes the specified separator character to prevent interference with special characters.
        filtered_text = self._filter_chars(text, exclude_chars=self._sep)
        len_text = len(filtered_text)

        if len_text != 1 and self._width >= len_text:
            raise KeyException(
                f"The provided 'width' value must be 1 less than the specified key length."
                "\nThis ensures that the separator is not automatically excluded, preventing unintended behavior."
            )

        sep_key = self._sep.join(
            textwrap.wrap(
                text=filtered_text,
                initial_indent=self._key_header,
                width=self._width,
            )
        )
        return sep_key

    def _generate_keys(self) -> Iterable[str]:
        num_keys = (
            2 if not self._num_of_keys else self._length_checker(self._num_of_keys)
        )

        def key_generator():
            return KeyCraftsman(
                num_of_keys=num_keys,
                key_length=self._key_length,
                exclude_chars=self._exclude_chars,
                include_all_chars=self._include_all,
                urlsafe_encoding=self._urlsafe,
            ).key

        keys_gen = (
            self._EXECUTOR().submit(key_generator) for _ in range(1, num_keys + 1)
        )
        keys = (k.result() for k in as_completed(keys_gen))
        return keys

    def _generate_key(self) -> Union[bytes, str]:
        key_length = self._length_checker(self._key_length)
        slicer = lambda *args: "".join(islice(*args, self._check_scale(key_length)))
        all_chars = slicer(cycle(self._ALL_CHARS))
        filtered_chars = self._filter_chars(all_chars, exclude_chars=punctuation)

        if self._include_all:
            filtered_chars = all_chars

        if self._exclude_chars:
            self._obj_instance(self._exclude_chars, obj_type=str)
            filter_char = partial(self._filter_chars, all_chars)
            exclude_chars_type = self.char_excluder(self._exclude_chars)
            filtered_chars = (
                filter_char(exclude_chars=exclude_chars_type)
                if exclude_chars_type
                else filter_char(exclude_chars=self._exclude_chars)
            )

        key_sample = SystemRandom().sample(
            population=filtered_chars, k=min(key_length, len(filtered_chars))
        )

        generated_key = "".join(key_sample)
        if self._urlsafe:
            generated_key = self._base64_key(generated_key.encode())
        return generated_key

    @cached_property
    def key(self) -> Union[bytes, str]:
        if self._key is None:
            self._key = self._generate_key()
            if any((self._sep, self._key_header)):
                self._key = self._wrap_text(text=self._key)
        return self._key

    @cached_property
    def keys(self) -> dict[str, bytes]:
        if self._keys is None:
            self._keys = self._generate_keys()
            if any((self._sep, self._key_header)):
                self._keys = map(self._wrap_text, self._keys)

            self._keys = {
                f"key-{idx}": key for idx, key in enumerate(self._keys, start=1)
            }
        return self._keys

    @cache
    def _get_file(self, default_name: str = "generated_key", ext: str = "bin") -> Path:
        fp_name = self._obj_instance(self._kfile_name, obj_type=str) or default_name
        ext = "." + ext
        file = (Path.cwd() / fp_name).with_suffix(ext)
        if not self._overwrite and all((file.is_file(), file.is_absolute())):
            id_trail = "ID" + str(id(0))[:5]
            file = file.with_name(f"{fp_name}_{id_trail}").with_suffix(ext)
        return file

    def _export_message(self, fp) -> None:
        print(
            f"\033[34m{fp.resolve().as_posix()!r}\033[0m has successfully been exported."
        )

    def export_key(self) -> None:
        fp = self._get_file()
        with open(fp, mode="w", encoding="utf-8") as key_file:
            key_file.write(self.key)
        self._export_message(fp)

    def export_keys(self) -> None:
        fp = self._get_file(default_name="generated_keys", ext="json")
        keys = self.keys

        def dump_file(data):
            with open(fp, mode="w") as keys_file:
                json.dump(data, keys_file, indent=4)

        try:
            dump_file(keys)

        except json.JSONDecodeError as json_error:
            raise KeyException(
                f"Error occurred while encoding the data to JSON: {json_error}."
                "\nPlease ensure that the data is properly formatted for JSON encoding."
            )
        except Exception as e_error:
            print(
                KeyException(
                    f"An unexpected error occurred: {e_error}."
                    "\nPlease review your parameter configurations for potential issues."
                    "\nIf special characters are included, all keys will be decoded for serialization compatibility."
                )
            )
            if self._urlsafe:
                keys = {k: v.decode() for k, v in keys.items()}
            dump_file(keys)
        finally:
            self._export_message(fp)


def excluder_chart() -> Union[dict[str, str], str, None]:
    """
    This function returns a dictionary containing all possible exclude types for the `exlude_chars` parameter.

    - The keys in the dictionary represent the possible exclude types.
    - The values in the dictionary represent the character sets to be excluded from the generated key.
    - The character sets are based on the ASCII letters, digits, and punctuation characters.
    - Whitespace characters ((space)\\t\\n\\r\\v\\f) are automatically excluded from the charset.
    """
    return KeyCraftsman.char_excluder(return_chart=True)


def generate_fernet_keys(
    num_of_keys: int = None,
    exclude_chars: str = "",
    include_all_chars: bool = False,
    keyfile_name: str = "",
    overwrite_keyfile: bool = False,
) -> Union[bytes, dict[str, bytes]]:
    """
    Generate secure cryptographic key(s) using the `KeyCraftsman` class with customizable parameters.

    #### Parameters:
        - `key_header` (str): Initial indentation for each line in the key. Defaults to an empty string.
        - `include_all_chars` (bool): Include all ASCII letters, digits, and punctuation in the key. Defaults to False.
        - `keyfile_name` (str): Name of the file when exporting the key. Defaults to an empty string.
        - `overwrite_keyfile` (bool): If True, overwrite the key file if it already exists. Defaults to False.

    #### Returns:
        - `bytes`: The generated cryptographic key.

    #### Raises:
        - `KeyException`: If an error occurs during key generation or export.
    """
    # XXX `key_length` and `urlsafe_encoding` are hardcoded to ensure compatibility with Fernet encryption.
    secure_key = KeyCraftsman(
        key_length=32,
        urlsafe_encoding=True,
        num_of_keys=num_of_keys,
        exclude_chars=exclude_chars,
        include_all_chars=include_all_chars,
        keyfile_name=keyfile_name,
        overwrite_keyfile=overwrite_keyfile,
    )
    get_method = lambda k, m: getattr(k, m+"s" if num_of_keys else m)
    if any((keyfile_name, overwrite_keyfile)):
        get_method(secure_key, "export_key")
    return get_method(secure_key, "key")


# XXX Metadata Information
METADATA = {
    "version": (__version__ := "1.0.2"),
    "license": (__license__ := "Apache License, Version 2.0"),
    "url": (__url__ := "https://github.com/yousefabuz17/KeyCraftsman"),
    "author": (__author__ := "Yousef Abuzahrieh <yousef.zahrieh17@gmail.com"),
    "copyright": (__copyright__ := f"Copyright © 2024, {__author__}"),
    "summary": (
        __summary__ := "A Python class for generating secure and customizable keys."
    ),
    "doc": (__doc__ := KeyCraftsman.__doc__),
}


__all__ = (
    "METADATA",
    "KeyCraftsman",
    "KeyException",
    "excluder_chart",
    "generate_fernet_keys",
)
