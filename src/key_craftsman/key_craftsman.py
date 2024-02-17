import base64
import re
import sys
import textwrap
from itertools import cycle, islice
from functools import cached_property, partial
from pathlib import Path
from secrets import SystemRandom
from string import (
    ascii_lowercase,
    ascii_letters,
    ascii_uppercase,
    digits,
    hexdigits,
    octdigits,
    punctuation,
    whitespace,
)
from typing import Any, Iterable, Union


class KeyException(BaseException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class KeyCraftsman:
    """
    KeyCraftsman is a Python class designed to generate secure and customizable keys.
    It offers features such as specifying key length, excluding characters, including all characters,
    URL-safe encoding, and more. The generated key can be exported to a file with optional formatting.
    """

    _ALL_CHARS: str = ascii_letters + digits + punctuation
    _MIN_CAPACITY: int = int(1e6)
    _MAX_CAPACITY: int = sys.maxsize
    _MAX_LENGTH: int = _MAX_CAPACITY // 10

    def __init__(
        self,
        key_length: int = 32,
        exclude_chars: str = "",
        include_all_chars: bool = False,
        urlsafe_encoding: bool = False,
        initial_key_header: str = "",
        width: int = 4,
        keyfile_name: str = "",
        export_key: bool = False,
        sep: str = "",
    ) -> None:
        self._key_length = key_length
        self._exclude_chars = exclude_chars
        self._include_all = include_all_chars
        self._urlsafe = urlsafe_encoding
        self._initial_indent = initial_key_header
        self._width = width
        self._export_key = export_key
        self._kfile_name = keyfile_name
        self._sep = sep
        self._key = None

    @classmethod
    def _compiler(
        cls,
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
        except:
            raise

    @staticmethod
    def _filter_chars(s: str, *, exclude: str = "") -> str:
        """
        ### Filter characters in the given string, excluding those specified.

        #### Parameters:
            - `s` (str): The input string to be filtered.
            - `exclude` (str): Characters to be excluded from the filtering process.

        #### Returns:
            - str: The filtered string with specified characters excluded.

        #### Notes:
            - This method employs the `translate` method to efficiently filter characters.
            - To exclude additional characters, provide them as a string in the `exclude` parameter.
        """
        return "".join(s).translate(str.maketrans("", "", exclude))
    
    @staticmethod
    def _whitespace_checker(cls, key):
        if cls._compiler(key, (whitespace, "whitespace")):
            print(
                KeyException(
                    f"{whitespace = !r} is already excluded from the charset.\n"
                )
            )

    @classmethod
    def _char_excluder(
        cls, key: str = "punct", return_chart: bool = False
    ) -> Union[dict[str, str], str, None]:
        """
        ### Exclude specific character sets based on the provided key.

        #### Parameters:
        - key (str): The key to select the character set to exclude.
        - return_chart (bool): If True, returns the dicitonary containing all possible exluce types.

        #### Returns:
        - str: The selected character set based on the key to be excluded from the generated passkey.

        #### Possible values for key:
        - 'punct': Excludes punctuation characters.
        - 'ascii': Excludes ASCII letters (both uppercase and lowercase).
        - 'ascii_lower': Excludes lowercase ASCII letters.
        - 'ascii_upper': Excludes uppercase ASCII letters.
        - 'ascii_punct': Excludes both ASCII letters and punctuation characters.
        - 'ascii_lower_punct': Excludes both lowercase ASCII letters and punctuation characters.
        - 'ascii_upper_punct': Excludes both uppercase ASCII letters and punctuation characters.
        - 'digits': Excludes digits (0-9).
        - 'digits_ascii': Excludes both digits and ASCII letters.
        - 'digits_punct': Excludes both digits and punctuation characters.
        - 'digits_ascii_lower': Excludes both digits and lowercase ASCII letters.
        - 'digits_ascii_upper': Excludes both digits and uppercase ASCII letters.
        - 'digits_ascii_lower_punct': Excludes digits, lowercase ASCII letters, and punctuation characters.
        - 'digits_ascii_upper_punct': Excludes digits, uppercase ASCII letters, and punctuation characters.
        - 'hexdigits': Excludes hexadecimal digits (0-9, a-f, A-F).
        - 'hex_punct': Excludes hexadecimal digits and punctuation characters.
        - 'hex_ascii': Excludes hexadecimal digits and ASCII letters.
        - 'hex_ascii_lower': Excludes hexadecimal digits and lowercase ASCII letters.
        - 'hex_ascii_upper': Excludes hexadecimal digits and uppercase ASCII letters.
        - 'hex_ascii_punct': Excludes hexadecimal digits, ASCII letters, and punctuation characters.
        - 'hex_ascii_lower_punct': Excludes hexadecimal digits, lowercase ASCII letters, and punctuation characters.
        - 'hex_ascii_upper_punct': Excludes hexadecimal digits, uppercase ASCII letters, and punctuation characters.
        - 'octodigits': Excludes octal digits (0-7).
        - 'octo_punct': Excludes octal digits and punctuation characters.
        - 'octo_ascii': Excludes octal digits and ASCII letters.
        - 'octo_ascii_lower': Excludes octal digits and lowercase ASCII letters.
        - 'octo_ascii_upper': Excludes octal digits and uppercase ASCII letters.
        - 'octo_ascii_punct': Excludes octal digits, ASCII letters, and punctuation characters.
        - 'octo_ascii_lower_punct': Excludes octal digits, lowercase ASCII letters, and punctuation characters.
        - 'octo_ascii_upper_punct': Excludes octal digits, uppercase ASCII letters, and punctuation characters.

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
        reverse_chars = {v: v for v in all_chars.values()}
        if return_chart:
            return all_chars
        return all_chars.get(key) or reverse_chars.get(key)

    @classmethod
    def _repeat_value(cls, length) -> int:
        if length >= cls._MIN_CAPACITY:
            return cls._MAX_LENGTH
        return cls._MIN_CAPACITY

    @classmethod
    def _length_checker(cls, length):
        if any((not length, not isinstance(length, int))):
            raise KeyException("The key length must be a positive integer.")

        if length >= (max_length := cls._MAX_CAPACITY):
            raise KeyException(
                f"Key length exceeds the maximum allowed capacity of {max_length = !r} characters. "
                f"Received key with {length = !r}."
            )
        return length

    def _obj_instance(obj: Any, obj_type: Any = str):
        if not isinstance(obj, obj_type):
            raise KeyException(
                f"The provided value must be of type {obj_type}."
                f"Provided value {obj = !r}"
            )
        return obj

    @classmethod
    def _wrap_text(
        cls, text: str, initial_key_header: str = "", sep: str = "", width: int = None
    ):
        """
        Wrap text with a specified separator is not implemented in this program.

        This program currently does not support the usage of special characters as separators
        when wrapping text. If you require custom separators, please refrain from using
        special characters, and consider using standard separators.

        Parameters:
            - text (str): The input text to be wrapped.
            - initial_key_header (str): The initial indentation for each line.
            - sep (str): The specified separator (unsupported if containing special characters).
            - width (int): The desired width for text wrapping.

        Raises:
            KeyException: Raised when attempting to use special characters with custom separators.
        """
        if cls._compiler(text, punctuation):
            print(
                NotImplementedError(
                    "\n[SPECIAL CHARACTERS DETECTED]\n"
                    "This program is primarily designed to support separators with standard characters only. "
                    "To avoid potential issues, refrain from using special characters in separators. "
                    "If seperators required, consider using standard characters such as ascii_letters and digits (default)."
                    "\n"
                )
            )
        sep = cls._obj_instance(sep)
        initial_key_header = cls._obj_instance(initial_key_header)
        width = 4 if not width else cls._obj_instance(width, obj_type=int)
        filtered_text = cls._filter_chars(text, exclude=sep)
        sep_key = sep.join(
            textwrap.wrap(
                text=filtered_text, initial_indent=initial_key_header, width=width
            )
        )
        return sep_key

    @classmethod
    def _generate_key(
        cls,
        key_length: int = 32,
        *,
        exclude: str = "",
        include_all_chars: bool = False,
        urlsafe_encoding: bool = False,
    ) -> Union[bytes, str]:
        if all((exclude, include_all_chars)):
            raise KeyException(
                "Cannot specify both 'exclude' and 'include_all_chars' parameters."
            )

        key_length = cls._length_checker(key_length)
        slicer = lambda *args: "".join(islice(*args, cls._repeat_value(key_length)))
        all_chars = slicer(cycle(cls._ALL_CHARS))
        filtered_chars = cls._filter_chars(all_chars, exclude=punctuation)

        if include_all_chars:
            filtered_chars = all_chars

        if exclude:
            cls._obj_instance(exclude, obj_type=str)
            filter_char = partial(cls._filter_chars, all_chars)
            exclude_type = cls._char_excluder(exclude)
            filtered_chars = (
                filter_char(exclude=exclude)
                if not exclude_type
                else filter_char(exclude=exclude_type)
            )

        key_sample = SystemRandom().sample(
            population=filtered_chars, k=min(key_length, len(filtered_chars))
        )

        generated_key = "".join(key_sample)
        if urlsafe_encoding:
            generated_key = cls._base64_key(generated_key.encode())
        return generated_key

    @cached_property
    def key(self):
        if self._key is None:
            self._key = self._generate_key(
                key_length=self._key_length,
                exclude=self._exclude_chars,
                include_all_chars=self._include_all,
                urlsafe_encoding=self._urlsafe,
            )
            if any((self._sep, self._initial_indent)):
                self._key = self._wrap_text(
                    text=self._key,
                    sep=self._sep,
                    initial_key_header=self._initial_indent,
                    width=self._width,
                )
        return self._key

    def export_key(self):
        cwd = Path(__file__).parent
        fp_name = self._kfile_name or "generated_key"
        default_fp = (cwd / fp_name).with_suffix(".bin")
        if all((default_fp.is_file(), default_fp.is_absolute())):
            id_trail = "ID" + str(id(0))[:5]
            default_fp = default_fp.with_name(f"{fp_name}_{id_trail}")
        with open(default_fp.with_suffix(".bin"), mode="w") as key_file:
            key_file.write(self.key)
        print(
            f"\033[34m{default_fp.resolve().as_posix()!r}\033[0m has successfully been exported."
        )


# XXX Metadata Information
METADATA = {
    "version": (__version__ := "1.0.0"),
    "license": (__license__ := "Apache License, Version 2.0"),
    "url": (__url__ := "https://github.com/yousefabuz17/KeyCraftsman"),
    "author": (__author__ := "Yousef Abuzahrieh <yousef.zahrieh17@gmail.com"),
    "copyright": (__copyright__ := f"Copyright © 2024, {__author__}"),
    "summary": (
        __summary__ := "A Python class for generating secure and customizable keys."
    ),
    "doc": __doc__,
}


__all__ = (
    "METADATA",
    "KeyCraftsman",
    "KeyException",
)
