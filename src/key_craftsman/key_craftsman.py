import base64
import json
import math
import logging
import operator
import re
import sys
import textwrap
import uuid
from collections import Counter, namedtuple
from concurrent.futures import as_completed, ThreadPoolExecutor
from functools import cache, cached_property, partial
from itertools import cycle, islice, tee
from logging import Logger
from pathlib import Path
from random import SystemRandom
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
from typing import Any, Iterable, Iterator, Literal, NamedTuple, Union


class FilterLog(logging.Filter):
    def __init__(self) -> None:
        self.logged = set()

    def filter(self, log: logging.LogRecord) -> bool:
        """
        This method filters out duplicate log messages to prevent redundant log entries.
        """
        if (error := log.getMessage()) not in self.logged:
            self.logged.add(error)
            return True


logger: Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    **{
        "fmt": "[%(asctime)s][%(levelname)s]:%(message)s",
        "datefmt": "%Y-%m-%d-T%I:%M:%S %p",
    }
)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
stream_handler.addFilter(FilterLog())
logger.addHandler(stream_handler)


class KeyException(BaseException):
    """
    A custom exception class derived from `BaseException` for managing errors associated with generating
    or exporting key(s). This exception should be raised when encountering issues in the process of
    generating or exporting keys within the application.

    #### Attributes:
    - `log_method` (Logger): The logging method to use for displaying the exception message.
    - `disable_color` (bool): A flag indicating whether to disable colored formatting in the log message.
    """

    def __init__(
        self,
        *args: tuple[str, ...],
        log_method: Logger = logger.critical,
        disable_color: bool = False,
    ) -> None:
        self.log_method = log_method
        super().__init__(*args)
        self.log_method(
            self
            if disable_color
            else "\033[{}m{}\033[0m".format(self._color_matcher(self.log_method), self)
        )

    @classmethod
    def _color_matcher(cls, log_method: Logger) -> Literal["34", "33", "31"]:
        """
        Match the log method to the corresponding color code for the log message.

        #### Parameters:
            - `log_method` (Logger): The logging method to use for displaying the exception message in a specific color.

        #### Returns:
            - `str`: The color code for the log message.

        #### NOTE::

        - The color code is used to format the log message in a specific color based on the log method.
        - All critical messages are raised with no color by default.
        """
        log_type = cls._get_type(log_method)
        if log_type == "debug":
            color = "32"
        elif log_type == "info":
            color = "34"  # Blue
        elif log_type == "warning":
            color = "33"  # Yellow
        else:
            # ** log_type in ("error", "critical")
            color = "31"  # Red
        return color

    @staticmethod
    def _get_type(log: Logger) -> str:
        return re.search(r"\.\w+", str(log)).group().lstrip(".")


class KeyCraftsman(Iterable):
    """
    `KeyCraftsman` is a modernized and innovative Python class designed to generate passcodes to your own liking.
    It offers features such as specifying key length, excluding characters, including all characters, URL-safe encoding, and more.
    The generated passkey(s) can be exported to a file for future use.

    #### Features:
        - **Passkey Generation**: Generate secure and customizable keys with various parameters.
        - **Passkey Length**: Specify the length of the generated keys.
        - **Exclude Characters**: Exclude specific characters from the generated keys.
        - **Include All Characters**: Include all ASCII letters, digits, and punctuation in the generated keys.
        - **Unique Characters**: Ensure that the generated key(s) or word(s) contain unique characters.
        - **URL-Safe Encoding**: Utilize URL-safe base64 encoding for generated keys.
        - **Export Passkey(s)**: Export the generated key(s) to a file with optional formatting.
        - **Custom Text Wrapping**: Wrap the generated key with a custom separator and width.
        - **Multiple Passkey Generation**: Generate multiple keys with a single instance.
        - **Word Generation**: Generate words using the `random.SystemRandom()` method.
        - **Verbose Mode**: Enable or disable verbose mode for logging and printing exceptions.
        - **Custom Passkey File Name**: Specify a custom name for the exported key file.
        - **Overwrite Passkey File**: Overwrite the key file if it already exists.
        - **Exclusion Chart**: Print and export the exclusion chart for help in excluding characters.
        - **RFC 4122 Compliant UUID**: Generate an RFC 4122 compliant UUID using the `kc_uuid` function.

    #### Parameters:
        - `key_length` (int): The length of the generated key. Defaults to 16.
            - The key length must be a positive integer.
            - The maximum capacity is determined by the system's maximum integer size.
        - `exclude_chars` (Union[int, str]): Characters to exclude from the generated key.
            - If not specified, only punctuation characters will be excluded.
            - Please refer to the `Exclusions Chart` from the documentation for reference.
            - Whitespace characters are automatically excluded from the charset.
            - The input can be a string key type or index value from the exclusion chart.
            - `Examples`:
                - Excluding specific characters:
                    - `exclude_chars="punct"` will exclude punctuation characters from the generated key.
                    - `exclude_chars="octo_ascii_upper_punct"` will exclude octal digits, uppercase ASCII letters, and punctuation characters.
                    - `exclude_chars=1` will exclude punctuation characters from the generated key.
                    - `exclude_chars=29` will exclude octal digits, uppercase ASCII letters, and punctuation characters.
        - `include_all_chars` (bool): Whether to include all characters (ASCII letters, digits, and punctuation).
        - `unique_chars` (bool): Whether to ensure that the generated key contains unique characters.
            - This feature is useful for generating unique keys for specific use cases.
            - If the key length is larger than the length of the unique character set, an exception will be raised.
            - If the generated key is already unique, a warning message will be printed in verbose mode.
            - If the unique character limit is bypassed, a warning message will be printed in verbose mode.
        - `bypass_unique_limit` (bool): Whether to bypass the unique character limit.
        - `encoded` (bool): Whether to encode the the generated key(s).
        - `urlsafe-encoded` (bool): Whether to use URL-safe base64 encoding. Defaults to False.
            - If True, the generated key will be encoded using URL-safe base64 encoding (`base64.urlsafe_b64encode`).
        - `num_of_keys` (int): Number of keys to generate when using `export_keys()`.
            - If not specified, the default number of keys is 2.
            - The maximum number of keys is determined by the system's maximum integer size.
        - `use_words` (bool): Wether to use words for key generation.
            - `num_of_words` (int): Number of words to generate using `random.SystemRandom()`.
                #### NOTE::

                - `num_of_words` parameter will be ignored if `use_words` is disabled.

        - `sep` (str): The specified separator for text wrapping.
            - If not specified, the key will not be wrapped with a separator.
            - It is recommended to use one character of any standard characters for the separator (e.g., ascii_letters, digits).
            - The length of the separator must be 1 unless using `use_words`.
            - `sep_width` (Union[int, Iterable]): Width for text wrapping when using separators.
                - If not specified:
                    - The default width is 4 if using keys and not words.
                    - The default width is the length of the word divided by 2 if using words.
                - The width is only applicable when using separators.
                - The width must be 1 less than the key length to prevent the separator from being excluded.
                - XXX Examples:
                    - `sep=":"` will wrap the generated key with a colon separator.
                    - `sep_width=4` will wrap the generated key with a colon separator and a width of 4.
                    - `sep_width=(1, 5, 7)` will wrap the generated key with a colon separator at indexes 1, 5, and 7.
        - `keyfile_name` (str): Name of the file when exporting key(s).
            - If not specified, a default file name will be used.
            - The default file name is 'generated_key(s)'.
            - The file extension will be '.bin' for single keys and '.json' for multiple keys.
            - If the file exists and:
                - `overwrite_keyfile` is False, a unique file name will be generated.
                    - 'generated_key(s)_ID<int>.bin' or 'generated_key(s)_ID<int>.json'
                - `overwrite_keyfile` is True, the existing file will be overwritten.
        - `overwrite_keyfile` (bool): Whether to overwrite the key file if it already exists.
            - If False, a unique file name will be generated to avoid overwriting the existing file.
            - If True, the existing file will be overwritten with the new key(s).
        - `verbose` (bool): Whether to enable verbose mode for printing exceptions.
            - If True, info and warning messages will be enabled.
            - If False, no messages will be printed if False.
            #### NOTE::

            - Messages will only be printed to the console but not be logged to a file.
            - The logger is intended for stream handling only.

    #### Attributes:
        - `key`: Cached property to retrieve a single generated key.
        - `keys`: Cached property to retrieve a dictionary of multiple generated keys.
        - `_ALL_CHARS`: Class attribute containing all ASCII letters, digits, and punctuation.
        - `_MIN_CAPACITY`: Class attribute defining the minimum key capacity (Value: 100_000)
        - `_MAX_CAPACITY`: Class attribute defining the maximum key capacity (Value: 9_223_372_036_854_775_807)
        - `_EXECUTOR`: Class attribute for the ThreadPoolExecutor.

    #### Methods:
        - `export_key()`: Exports the generated key to a file.
        - `export_keys()`: Exports multiple generated keys to a JSON file.

    #### Raises:
        - `(V)` (Verbose Mode Enabled):
            - Will not raise but messages will only be printed to the console but not be logged to a file.
            - Message types include:
                - `Info`
                - `Warning`
                - `Error`
                - `Critical`
        - `StopIteration`: When iterating over the class key(s).
        - `KeyException`: When encountering issues during key generation or exportation.
            - If any of the parameter types are invalid:
                - Positive Integer (int):
                    - `key_length` # Must be less than the maximum capacity.
                    - `num_of_keys`
                    - `num_of_words` # Must be less than the maximum capacity.
                - String (str):
                    - `sep` # Must be a single character.
                    - `keyfile_name`
                - Boolean (bool):
                    - `unique_chars`
                    - `bypass_unique_limit`
                    - `include_all_chars`
                    - `encoded`
                    - `urlsafe_encoded`
                    - `use_words`
                    - `overwrite_keyfile`
                    - `verbose`
                - Union[int, str]:
                    - `exclude_chars` # Example: "punct" or 1
                - Iterable (Union[int | str, Iterable]):
                    - `sep_width`
            - If any of the following parameters are mutually exclusive:
                - `exclude_chars` and `include_all_chars`
                - `encoded` and `urlsafe_encoded`
            - If any of the following exceeds the maximum capacity:
                - `key_length`
                - `num_of_keys`
                - `num_of_words`
            - When the specified separator length is greater than 1.
            - When special characters are detected in the generated key when wrapping with the specified `sep`.
            - When the specified 'sep_width' value is not 1 less than the specified key length.
            - When `unique_chars` is enabled and the key length is larger than the length of the unique character set.
            - When `use_words` is enabled and the `num_of_words` parameter is not specified.
            - When trying to exclude all string characters (ASCII letters + digits + punctuation)
            - (V) When the specified separator contains prohibited whitespace characters (excluding single space).
            - (V) When special characters are detected in the text when wrapping.
            - (V) When `unique_chars` is enabled and the generated key is already unique.
            - (V) When attempting to serialize the generated keys to a JSON file.
            - (V) When the default or specified key file already exists and `overwrite_keyfile` is False.
            - (V) When exporting the generated key(s) to a file.

    #### Usage Examples:
        ```python
        # Generate encoded or URLSafe-encoded keys.
        key_gen = KeyCraftsman(key_length=32, num_of_keys=2, include_all_chars=False, encoded=True)

        key = key_gen.key # Retrieve a single encoded generated key.
        # Output: b'...'
        keys = key_gen.key # or retrieve a dictionary of multiple encoded generated keys from the same instance.
        # Output: {'key-1': b'...', 'key-2': b'...'}
        --------------------------------------------------------
        key_gen.export_key() # Export the generated key to a file.
        # Output: 'generated_key.bin has successfully been exported.'
        --------------------------------------------------------
        key_gen.export_keys() # Export multiple generated keys to a JSON file.
        # Output: 'generated_keys.json has successfully been exported.'
        --------------------------------------------------------
        # Class can be iterated over the key(s) depending on if parameter 'num_of_keys' is passed in.

        for k in key_gen:
            # If 'num_of_keys' is not passed in, the class will iterate over the generate key.
            # <single character from single generated key>
            # or
            # If 'num_of_keys' is passed in, the class will over the dictionary values of the generated keys.
            # <single generated key from the dictionary>
            print(k)
        # Alternatively, the class can be iterated over using the `__next__` method.
        print(next(key_gen)) # Output: <single character from single generated key>
        --------------------------------------------------------
        # Print the class object
        # Print and export the exclusion chart for help in excluding characters.
        print(key_gen) # Output: '<__main__.KeyCraftsman object at 0x7f7f7f7f7f7f>'
        print(key_gen.print_echart(return_table=True)) # Output: PrettyTable object of the Exclusions Chart.
        print(key_gen.print_echart(fp="exclusions_chart.txt")) # Output: Exclusions Chart exported to 'exclusions_chart.txt'.
        --------------------------------------------------------
        # Custom text wrapping with a separator.
        key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=4)
        key = key_gen.key # Retrieve a single generated key.
        # Output: '...:...:...:...'
        --------------------------------------------------------
        # Custom text wrapping with a separator and encoding.
        key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=4, encoded=True)
        key = key_gen.key # Retrieve a single generated key.
        # Output: b'...:...:...:...'
        --------------------------------------------------------
        # Custom text wrapping with a separator and URL-safe encoding.
        key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=4, urlsafe_encoded=True)
        key = key_gen.key # Retrieve a single generated key.
        # Output: b'...'
        --------------------------------------------------------
        # Generate words using the with a custom separator.
        key_gen = KeyCraftsman(num_of_words=2, sep="/", use_words=True)
        word = key_gen.key # Retrieve a single generated word.
        # Output: '...../.....'
        keys = key_gen.keys # Retrieve a dictionary of multiple generated words.
        # Output: {'key-1': '...../.....' 'key-2': '...../.....'
        --------------------------------------------------------
        # Exclude specific characters from the generated key.
        key_gen = KeyCraftsman(exclude_chars="abc#%()1")
        # Output: 'd2e3f4g5h6i7j8k9l0mno' # Excludes 'abc#%()1'
        --------------------------------------------------------
        # or exclude using the exclusion chart key.
        key_gen.print_echart(return_chart=True)
        # Output: Exclusions Chart (`PrettyTable`) for reference.
        --------------------------------------------------------
        # Exclude based on the exclusion chart option key or index value (e.g., 1-29).
        key_gen = KeyCraftsman(exclude_chars="punct")
        key_gen = KeyCraftsman(exclude_chars=1) # Excludes punctuation characters ("punct").
        --------------------------------------------------------
        # Generate unique keys with a custom separator.
        key_gen = KeyCraftsman(unique_chars=True)
        key = key_gen.key # Retrieve a single generated key.
        # Output: '...' # Unique characters are ensured in the generated key.
        --------------------------------------------------------
        # Generate key(s) with an iterable separator width.
        key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=(1, 5, 7))
        key = key_gen.key # Retrieve a single generated key.
        # Output: '.:...:.:.....'
        --------------------------------------------------------
        # Generate a RFC 4122 compliant key using the `kc_uuid` function with a custom version.
        # Which then will be passed into an `uuid.UUID` object.
        kc_id = kc_uuid(version: int = None)
        ```
    """

    _ALL_CHARS: str = ascii_letters + digits + punctuation
    _ALL_CHARS_LEN: int = len(_ALL_CHARS)
    _MIN_CAPACITY: int = int(1e5)
    _MAX_CAPACITY: int = sys.maxsize
    _UNIQUE_DISABLED: dict[str, int] = {"ascii_punct": 10, "oct_ascii_punct": 2}
    _EXECUTOR = ThreadPoolExecutor

    def __init__(
        self,
        key_length: int = 16,
        exclude_chars: Union[int, str] = "",
        include_all_chars: bool = False,
        unique_chars: bool = False,
        bypass_unique_limit: bool = False,
        encoded: bool = False,
        urlsafe_encoded: bool = False,
        num_of_keys: int = None,
        num_of_words: int = None,
        sep: str = "",
        sep_width: Union[int, Iterable[int]] = None,
        keyfile_name: str = "",
        use_words: bool = False,
        overwrite_keyfile: bool = False,
        verbose: bool = False,
    ) -> None:
        logger.disabled = not verbose

        self._key_length = key_length
        self._exclude_chars = exclude_chars
        self._include_all = include_all_chars
        self._encoded = encoded
        self._urlsafe = urlsafe_encoded
        self._unique_chars = unique_chars
        self._bypass_unique = bypass_unique_limit
        self._num_of_keys = num_of_keys
        self._num_of_words = num_of_words
        self._width = sep_width
        self._kfile_name = keyfile_name
        self._overwrite = overwrite_keyfile
        self._use_words = use_words
        self._sep = self._check_sep(sep, bypass_length=self._use_words)
        self._wrap_key = any((self._sep, self._width))
        self._encode_key = any((self._encoded, self._urlsafe))
        self._key = None
        self._keys = None
        self.__index = 0

        # -----------------------------
        # XXX - For internal use only.
        # '__class_keys' is a quick way to retrieve the generated key(s)
        # based on the 'num_of_keys' or 'num_of_words' parameter.
        # Instead of using the 'key' or 'keys' property, '__class_keys' can be used to retrieve the key(s).
        self.__class_keys: Union[bytes, str, tuple[bytes], tuple[str]] = lambda: self.unpack(
            _get_method(
                self, attr="key", status=any((self._num_of_keys, self._num_of_words))
            )
        )
        # XXX - Return value ('Union[bytes, str, tuple[str]]')
        # Is a single key or multiple keys  is based on whether 'num_of_keys' or 'num_of_words' is passed in.
        # -----------------------------

        # XXX - Check for mutually exclusive parameters.
        self._check_combos(
            (self._exclude_chars, self._include_all),
            names=("exclude_chars", "include_all_chars"),
        )

        self._check_combos(
            (self._encoded, self._urlsafe), names=("encoded", "urlsafe_encoded")
        )

    def __repr__(self) -> str:
        """Returns a sample of generated keys"""
        return "\n".join(KeyCraftsman(key_length=12, sep="-", num_of_keys=10))

    def __str__(self) -> str:
        cls_obj = self.__class__
        return f"<{cls_obj.__module__}.{cls_obj.__name__} object at {hex(id(self))}>"

    def __iter__(self) -> Iterator[Union[bytes, str]]:
        """
        Iterates over the generated key(s).
        - If 'num_of_keys' is not passed in, the class will iterate over a single generate key.
        - If 'num_of_keys' is passed in, the class will over the dictionary values of the generated keys.
        """
        return iter(self.__class_keys())

    def __next__(self) -> Union[bytes, str]:
        """
        #### Raises:
            - `StopIteration`:
                - Raised when all key(s) have been iterated. To prevent this exception,
                ensure to check the iteration status using the `.index` attribute before calling `__next__`,
                or consider increasing the number of keys to iterate over.
                - Iteration values soley depends on whether 'num_of_keys' is passed in.

        """
        try:
            # XXX - Iterates over generated key(s).
            next_key = self.__class_keys()[self.__index]
            self.__index += 1
            return next_key
        except IndexError:
            raise StopIteration(
                "[STOP-ITERATION]\n"
                "All keys have been iterated. "
                "Please make sure to check the iteration status ('.index') before calling '__next__'. "
                "Otherwise, increase the number of keys to iterate over."
            )

    @property
    def index(self) -> int:
        """
        #### Returns:
            - `int`: The current index value for the iteration.

        #### Notes:
            - The index value is used to keep track of the current iteration status.
            - It is recommended to check the index value before calling `__next__`.
            - The index value is reset to 0 after all key(s) have been iterated.
        """
        return self.__index
    
    @cached_property
    def max_index(self):
        chart = self.char_excluder(return_chart=True)
        return Counter(chart.items()).total()

    @classmethod
    def _validate_ktuple(cls, ktuple: NamedTuple) -> Union[NamedTuple, bool]:
        """
        Validate the namedtuple object.

        #### Parameters:
            - `ktuple` (NamedTuple): The namedtuple object to validate.

        #### Returns:
            - `bool`: The object if the object is a `KeyCraftsman.Keys` namedtuple; False otherwise.
        """
        if hasattr(ktuple, "_fields") and all(
            (
                cls._obj_instance(ktuple, tuple),
                cls._obj_instance(ktuple._fields, tuple),
                hasattr(ktuple, "__module__"),
                ktuple.__module__ == cls.__name__,
                ktuple.__class__.__name__ == "Keys",  # XXX - NamedTuple class name.
            )
        ):
            return ktuple
        return False

    @classmethod
    def unpack(cls, x: Any) -> Union[tuple[str], Any]:
        """
        Unpack the `KeyCraftsman.Keys` namedtuple object.

        #### Parameters:
            - `x` (Any): The namedtuple object to unpack.

        #### Returns:
            - `Any`: The unpacked object if the object is not a `KeyCraftsman.Keys` namedtuple; the object itself otherwise.

        """
        return tuple(x._asdict().values()) if cls._validate_ktuple(x) else x

    @staticmethod
    def _check_combos(
        *args, method: Any = all, names: tuple[str] = None, check_only: bool = False
    ) -> bool:
        """Check for mutually exclusive parameters."""
        if result := method(*args):
            if not check_only:
                raise KeyException(
                    "Parameters ({!r}) are mutually exclusive.".format(", ".join(names))
                )
            return result

    @staticmethod
    def _pretty_table() -> tuple:
        """
        Check if the package 'prettytable' is installed and return the required objects.
        """
        try:
            from prettytable import PrettyTable, SINGLE_BORDER  # type: ignore
        except ImportError:
            # Disable the logger to forcefully print the error message to the console.
            logger.disabled = False
            KeyException(
                "[MISSING PACKAGE]\n"
                "Please be advised the package 'prettytable.PrettyTable' is currently not installed. "
                "The package is not required for the main functionality of the class "
                "but provides the exclusion chart for help in excluding characters "
                "and checking the unique max key size and the entropy level for each exclusion type."
                "\nTo install the package, for a more user-friendly experience, use the following command:"
                "\n\n$ pip install prettytable\n"
                "For more information,"
                "\nplease visit the official documentation at: https://pypi.org/project/prettytable/",
                log_method=logger.error,
            )
            return
        return SINGLE_BORDER, PrettyTable

    @classmethod
    def print_echart(
        cls, fp: Union[Path, str] = None, return_table: bool = False, **kwargs
    ) -> Any:
        """
        Print and export the exclusion chart for help in excluding characters.

        #### Parameters:
            - `fp` (Union[Path, str]): The file path to export the exclusion chart.
                - If not specified, the exclusion chart will be printed to the console.
            - `return_table` (bool): If True, returns the exclusion chart as a `PrettyTable` object.
                - If False, the exclusion chart will be printed to the console.
            - `**kwargs`: Additional keyword arguments for the `PrettyTable.get_string()` object.

        #### Returns:
            - `PrettyTable`: The exclusion chart as a `PrettyTable` object.
        """

        char_chart = cls.char_excluder(return_chart=True)

        def _k_extract(
            e: str = "", setify: bool = False, s=None
        ) -> Union[str, tuple[int, float]]:
            """Extract a key sample for each exclusion type."""
            if setify:
                set_key = set(s)
                entropy = cls.calculate_entropy(set_key)
                return (len(set_key), entropy)

            # Large key length to ensure all characters are included.
            sample_key = cls(key_length=500, exclude_chars=e)
            return sample_key.key

        key_samples = {}
        for idx, k in enumerate(char_chart, start=1):
            sample = _k_extract(e=k)
            unique_size = "{} ({:.2f})".format(*(_k_extract(s=sample, setify=True)))
            if k in cls._UNIQUE_DISABLED:
                k += " (UD)"
            # XXX - Store the key samples and the unique size for each exclusion type.
            # The unique size is the length of the unique characters and the entropy level.
            # The sample passkey is sliced to 16 characters for display purposes.
            key_samples[idx] = (k, sample[:16], unique_size)

        # XXX - Initiate and check if the package 'prettytable' is installed.
        pt = cls._pretty_table()
        if not pt:
            # If the package is not installed,
            # return the exclusion chart as a dictionary.
            return key_samples

        # If the package is installed,
        # return the exclusion chart as a `PrettyTable` object.
        single_border, pretty_table = pt

        table = pretty_table(
            ["Key-Options", "Key-Samples", "Unique Max Key-Size (Entropy)"]
        )
        table.set_style(single_border)

        for ks in key_samples.values():
            table.add_row(ks, divider=True)

        table.add_autoindex("Index")
        table.align["Index"] = "c"
        t = kwargs.pop("title", "Exclusions Chart (UD = Unique Disabled)")
        if return_table:
            table.title = t
            return table

        if fp:
            cls._obj_instance(fp, obj_type=(Path, str))
            if isinstance(fp, Path):
                fp = Path(fp).stem
            fp = open(fp, mode="w")

        print(table.get_string(title=t, **kwargs), file=fp)
        if fp:
            cls._export_message(fp=fp)
        sys.exit()

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
    def _base64_key(
        key: str, base_type: Literal["encode", "decode"] = "encode"
    ) -> bytes:
        base = [base64.urlsafe_b64decode, base64.urlsafe_b64encode][
            base_type == "encode"
        ]
        try:
            return base(key)
        except Exception as e_error:
            bt = base_type[:-1] + "ing"  # Encoding or Decoding
            raise KeyException(
                "[INVALID BASE64-CODING]\n"
                f"An error occurred during base64 {bt}:"
                f"\n{e_error}"
            )

    @classmethod
    def _filter_chars(
        cls,
        chars: str,
        *,
        include_chars: str = "",
        exclude_chars: str = "",
    ) -> str:
        """
        Filter characters in the given string, excluding those specified.

        #### Parameters:
            - `chars` (str): The input string to be filtered.
            - `include_chars` (str):
                - Characters to be included in the character set.
                - Characters will be filtered out from the filtering process.
            - `exclude_chars` (str): Characters to be excluded from the character set.

        #### Returns:
            - `str`: The filtered string with specified characters included or excluded.

        #### NOTE::

            - This method employs the `translate` method to efficiently filter characters.
            - To exclude additional characters, provide them as a string in the `exclude_chars` parameter.
        """

        # XXX - Validate all parameter instances.
        cls._obj_instance(chars, obj_type=(bytes, str))
        cls._obj_instance(include_chars, obj_type=(str))
        cls._obj_instance(exclude_chars, obj_type=(int, str))

        if isinstance(exclude_chars, str):
            if exclude_chars == cls._ALL_CHARS:
                # Excluding all characters (ascii_letters + digits + punctuation) is prohibited.
                raise KeyException(
                    "[INVALID EXCLUSION-TYPE]\n"
                    "Excluding all characters is prohibited. "
                    "Please specify a valid exclusion type or index value."
                    "\nFor help, use the `print_echart()` method or `excluder_chart` function "
                    "to view the exclusion chart for reference."
                )
            ws = whitespace
            sjoin = "".join
            if include_chars:
                # Removes all characters except those specified in the `include_chars` parameter.
                # Including a single space from whitespace is prohibited.
                single_space = " "
                ws = whitespace.strip(
                    single_space if single_space in include_chars else ""
                )
                exclude_chars: set = operator.sub(
                    *(map(set, (exclude_chars, include_chars)))
                )
            return sjoin(str(chars)).translate(
                str.maketrans("", "", ws + sjoin(exclude_chars))
            )

        return chars

    @classmethod
    def _whitespace_checker(cls, key: str, show_msg: bool = True) -> bool:
        """Check if the specified key contains whitespace characters."""
        cls._obj_instance(key, obj_type=str)
        key = key.lower()
        if key == "whitespace" or cls._compiler(key, whitespace, escape_k=False):
            if show_msg:
                KeyException(
                    f"{whitespace = } is already excluded from the charset.\n",
                    log_method=logger.warning,
                )
            return True
        return False

    @classmethod
    def _punctuation_checker(cls, key: str, **kwargs) -> bool:
        """Check if the specified key contains punctuation characters."""
        return bool(cls._compiler(key, punctuation, **kwargs))

    @classmethod
    @cache
    def char_excluder(
        cls,
        key: Union[int, str] = "punct",
        return_chart: bool = False,
        include_index: bool = False,
    ) -> Union[dict[str, str], str, None]:
        """
        Exclude specific character sets based on the provided key.

        #### Parameters:
            - `key` (str): The key to select the character set to exclude_chars.
            - `return_chart` (bool): If True, returns the dicitonary containing all possible exluce types.

        #### Returns:
            - `str`: The selected character set based on the key to be excluded from the generated passkey.

        #### Possible values for key:
            - `punct`: Excludes punctuation characters.
            - `ascii`: Excludes ASCII letters (both uppercase and lowercase).
            - `ascii_lower`: Excludes lowercase ASCII letters.
            - `ascii_upper`: Excludes uppercase ASCII letters.
            - `ascii_punct`: Excludes both ASCII letters and punctuation characters.
            - `ascii_lower_punct`: Excludes both lowercase ASCII letters and punctuation characters.
            - `ascii_upper_punct`: Excludes both uppercase ASCII letters and punctuation characters.
            - `digits`: Excludes digits (0-9).
            - `digits_ascii`: Excludes both digits and ASCII letters.
            - `digits_punct`: Excludes both digits and punctuation characters.
            - `digits_ascii_lower`: Excludes both digits and lowercase ASCII letters.
            - `digits_ascii_upper`: Excludes both digits and uppercase ASCII letters.
            - `digits_ascii_lower_punct`: Excludes digits, lowercase ASCII letters, and punctuation characters.
            - `digits_ascii_upper_punct`: Excludes digits, uppercase ASCII letters, and punctuation characters.
            - `hexdigits`: Excludes hexadecimal digits (0-9, a-f, A-F).
            - `hex_punct`: Excludes hexadecimal digits and punctuation characters.
            - `hex_ascii`: Excludes hexadecimal digits and ASCII letters.
            - `hex_ascii_lower`: Excludes hexadecimal digits and lowercase ASCII letters.
            - `hex_ascii_upper`: Excludes hexadecimal digits and uppercase ASCII letters.
            - `hex_ascii_punct`: Excludes hexadecimal digits, ASCII letters, and punctuation characters.
            - `hex_ascii_lower_punct`: Excludes hexadecimal digits, lowercase ASCII letters, and punctuation characters.
            - `hex_ascii_upper_punct`: Excludes hexadecimal digits, uppercase ASCII letters, and punctuation characters.
            - `octodigits`: Excludes octal digits (0-7).
            - `octo_punct`: Excludes octal digits and punctuation characters.
            - `octo_ascii`: Excludes octal digits and ASCII letters.
            - `octo_ascii_lower`: Excludes octal digits and lowercase ASCII letters.
            - `octo_ascii_upper`: Excludes octal digits and uppercase ASCII letters.
            - `octo_ascii_punct`: Excludes octal digits, ASCII letters, and punctuation characters.
            - `octo_ascii_lower_punct`: Excludes octal digits, lowercase ASCII letters, and punctuation characters.
            - `octo_ascii_upper_punct`: Excludes octal digits, uppercase ASCII letters, and punctuation characters.
            - `rfc_4122`: Excludes characters that are compliant with RFC 4122.
            - `non_rfc_4122`: Excludes characters that are not compliant with RFC 4122.

        """
        cls._check_combos(
            (return_chart, include_index), names=("return_chart", "include_index")
        )
        # The index value for the character 'f' in the ASCII letters.
        # This is used for the `rfc_4122` and `non_rfc_4122` keys (UUID version 4 specification)
        char_f = ascii_lowercase.index("f")
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
            "rfc_4122": ascii_lowercase[:char_f] + ascii_uppercase + punctuation,
            "non_rfc_4122": ascii_lowercase[char_f:] + ascii_uppercase + punctuation,
        }

        idx_chars = {idx: v for idx, v in enumerate(all_chars.values(), start=1)}

        if return_chart:
            # Returns dict[str, str] containing all possible exlcude types.
            return all_chars
        elif include_index:
            # Returns dict[int, dict[str, str]] containing all possible exlcude types.
            return idx_chars

        # Check if the specified key is a valid exclusion key or index value.
        cls._obj_instance(key, obj_type=(int, str))
        len_chars = len(all_chars)
        if isinstance(key, str):
            # Check if the specified key contains whitespace characters.
            cls._whitespace_checker(key)
        elif isinstance(key, int):
            # Validate the specified index value.
            if not 1 <= key <= len_chars:
                raise KeyException(
                    "[INVALID EXCLUSION-INDEX]\n"
                    f"The specified index value is invalid; requires an integer value between 1 and {len_chars}."
                )

        # Check if the specified key is a valid exclusion option or index value.
        # Otherwise, returns None.
        return [all_chars.get(key), idx_chars.get(key)][isinstance(key, int)]

    def _sig_larger(self, *args, threshold: int = 0) -> NamedTuple:
        """
        Calculate the significant difference between two numerical values.

        The 'status' field indicates whether the absolute difference between the provided values
        is within the threshold (1e5). If 'status' is False, the 'threshold' field will be the maximum
        of the provided values and the threshold.
        """
        threshold = self._obj_instance(
            threshold, obj_type=(int, float), return_none=True
        )
        args
        if len(args) == 2:
            threshold = threshold or abs(self._MAX_CAPACITY - self._MIN_CAPACITY)
            Sig = namedtuple("SigLarger", ("status", "threshold"))
            abs_diff = abs(operator.sub(*args))
            status: bool = operator.le(*map(math.log1p, (abs_diff, threshold)))
            return Sig(status, max(max(args), threshold))
        raise KeyException(
            f"Excessive arguments provided; requires precisely two numerical values, such as {int} or {float}."
        )

    @classmethod
    def decode_key(
        cls, key: Union[bytes, str], encoding_type: Literal["default", "urlsafe"] = None
    ) -> Union[bytes, str]:
        """
        Decode the specified key based on the specified seperator and encoding type.

        #### Parameters:
            - `key` (Union[bytes, str]): The key to be decoded.
            - `encoding_type` (Literal["default", "urlsafe"]): The encoding type for the key.

        #### Returns:
            - `Union[bytes, str]`: The decoded key based on the specified encoding type.

        #### Raises:
            - `KeyException`:
                - If the key is not of type (`bytes`, `str`)
                - If the encoding type is not of type `Literal["default", "urlsafe"]`.
        """
        cls._obj_instance(key, obj_type=(bytes, str))
        if encoding_type:
            if encoding_type == "urlsafe":
                key = cls._base64_key(key, base_type="decode").decode()
            elif encoding_type == "default":
                key = key.decode()
            else:
                raise KeyException(
                    f"Invalid encoding type specified: {encoding_type = }. "
                    "The encoding type must be either 'default' or 'urlsafe'."
                )
        return key

    @classmethod
    def unique_test(
        cls,
        key: Union[bytes, Iterable, str],
        test_only: bool = False,
        seperator: str = "",
        encoding_type: Literal["default", "urlsafe"] = None,
    ) -> bool:
        """
        This method tests the uniqueness of the generated key.

        #### Parameters:
            - `key` (Union[bytes, Iterable, str]): The generated key to be tested for uniqueness.
            - `test_only` (bool): Whether to skip the filteration and decoding process.
            - `seperator` (str): The specified separator to filter out from the key for uniqueness testing.
            - `encoding_type` (Literal["default", "urlsafe"]): The encoding type for the key.

            #### NOTE::

            - If not specified correctly, the test will fail resulting in inaccurate results.

        #### Returns:
            - `bool`: True if the key is unique; False otherwise.

        #### Raises:
            - `KeyException`: If the key is not of type (`bytes`, `str`)

        #### Important Notes:
            - It is important to note the following:
                - Pass in `test_only` as True to skip the filteration and decoding process.
                - Otherwise:
                    - The method will use the specified seperator and encoding type to test the uniqueness of the key.
                    - As such, the method will not be able to accurately test the uniqueness of the key if not specified correctly.
                    - The test starts by doing the following:
                        - 1. Filtering out the specified separator.
                        - 2. If encoding type is specified, the key will be decoded.
                        - 3. The key will be checked by converting it to a set and comparing the length of the set to the length of the key.
            - If the key is unique, the method will return True; otherwise, it will return False.
        """
        cls._obj_instance(key, obj_type=Iterable)
        cls._obj_instance(seperator, obj_type=str)

        def test_key(k):
            return len(set(k)) == len(k)

        if test_only:
            # Skips the filteration and decoding process.
            return test_key(key)

        if encoding_type:
            key = cls.decode_key(key, encoding_type=encoding_type)
        key = cls._filter_chars(key, exclude_chars=seperator)
        return test_key(key)

    @classmethod
    def calculate_entropy(cls, text: str) -> float:
        """
        Calculates the entropy of the given text.

        #### Parameters:
            - `text` (str): The input text for which entropy is calculated.

        #### Returns:
            - `float`: The calculated entropy value.

        #### Raises:
            - `KeyException`: If the input text is not of type 'bytes' or 'str'.

        #### Notes:
        - This method computes the entropy of the input text, which provides a measure
        of the information content or uncertainty in the text.
        - The result is returned as a floating-point value.
        - The entropy calculation is based on the formula:
        >>> entropy = log2(length of text).

            - The logarithm is base 2, and the length of the text is used as the parameter.

        #### Example:
        >>> entropy_value = KeyCraftsman.calculate_entropy("example text")
        >>> print(entropy_value)
        4.169925001442312
        """
        cls._obj_instance(text, obj_type=(bytes, Iterable, str))
        # Calculate the entropy using the formula: entropy = log2(length of text)
        return math.log2(len(text))

    def _check_scale(self, length: int) -> int:
        """
        Checks and adjusts the scale of the 'itertools.cycle' value
        based on the specified key length.

        #### Parameters:
            - `length` (int): The length of the key for which the scale is checked and adjusted.

        #### Returns:
            - `int`: The adjusted key length based on the specified conditions.

        #### Notes:
        - This method evaluates the key length against certain criteria to determine
        the appropriate scaling factor for the 'itertools.cycle' mechanism.
        The key length is adjusted to ensure efficient and effective generation
        of cyclic keys within the specified constraints.

        #### Algorithm:
            - 1. Check if the key length is within the valid range.
            - 2. Assess if the key length is significantly larger than the specified range.
            - 3. Evaluate if the key length is significantly larger than the minimum capacity.
            - 4. Adjust the key length based on the assessed conditions.
        """

        # Check if the length is within the valid range
        self._length_checker(length)

        # Check if the length is significantly larger than the specified range
        large_length = self._sig_larger(length, abs(self._MAX_CAPACITY - length))

        # Check if the length is significantly larger than the minimum capacity
        rng_length = self._sig_larger(
            length, self._MIN_CAPACITY, threshold=self._ALL_CHARS_LEN
        )

        if length >= self._MIN_CAPACITY:
            # If the length is greater than or equal to the minimum capacity
            if large_length.status:
                # If the length is significantly larger than the specified range,
                # adjust the scale by doubling the length.
                return length * 2

            if rng_length.status:
                # If the length is within the appropriate cycle range for 'itertools.cycle'
                # and satisfies the condition specified by the threshold (length <= len(self._ALL_CHARS)),
                # it means the key can be efficiently generated using the cycling mechanism.
                # This ensures enough characters are present for the given key length.
                return length
            else:
                # Otherwise, return the absolute difference between MAX_CAPACITY and MIN_CAPACITY.
                return large_length.threshold
        return rng_length.threshold

    def _length_checker(self, length: int, obj: str = "key") -> int:
        invalid_len_str = "[INVALID LENGTH]\n"
        if not length or not isinstance(length, int):
            raise KeyException(
                f"{invalid_len_str}" f"The {obj} length must be a positive integer."
            )
        elif length >= (max_length := self._MAX_CAPACITY):
            raise KeyException(
                f"{invalid_len_str}"
                f"{obj.capitalize()} length exceeds the maximum allowed capacity of {max_length = } characters. "
                f"Received key with {length = }."
            )
        elif length >= (min_cap := self._MIN_CAPACITY):
            KeyException(
                f"{invalid_len_str}"
                f"The specified length exceeds the minimum capacity of {min_cap = }"
                f"Depending on the computer's specifications, significant processing power may be required.",
                log_method=logger.warning,
            )
        return length

    @staticmethod
    def _obj_instance(obj: Any, obj_type: Any = str, return_none: bool = False) -> Any:
        if return_none and not obj:
            # 'return_none' is implemented to allow for the return of 'None' if the object is empty.
            # In such cases, where the object is empty, the method will return 'None' and not raise an exception.
            return

        invalid_obj_str = "[INVALID OBJECT-INSTANCE]\n"
        if not isinstance(obj, obj_type):
            raise KeyException(
                f"{invalid_obj_str}"
                f"The provided value must be of type {obj_type}."
                f"\nProvided value {obj = } ({type(obj)!r})"
            )
        else:
            if obj_type in (Path, str):
                # Validate and return object if compatible with 'obj_type'.
                try:
                    obj = obj_type(obj)
                except Exception as e_error:
                    raise KeyException(
                        f"{invalid_obj_str}"
                        f"An error occured trying to convert {obj =} to {obj_type =}."
                        f"\n{e_error}"
                    )
        return obj

    def _check_sep(self, sep_val: str = "", bypass_length: bool = False) -> str:
        """
        Validates and filter the separator value for key generation.

        #### Args:
            - `sep_val` (str): The separator value to be validated and processed.

        #### Raises:
        - `KeyException`: Raised if any of the following:
            - Invalid separator length (>=1) when not using words.
            - Separator contains prohibited whitespace characters (excluding single space).

        #### Returns:
            - `str`: The filtered separator value.
        """

        if not sep_val:
            # If no separator is specified, return an empty string.
            return ""

        self._obj_instance(sep_val, obj_type=str)
        if not bypass_length and not (sep_length := len(sep_val)) <= 1:
            raise KeyException(
                "[INVALID SEP-LENGTH]\n"
                "The separator must have a fixed length of 1. "
                "This constraint is essential to prevent interference with separator placement when a width is specified."
                f"\n>>> ({sep_length = }) != 1",
                log_method=logger.error,
            )

        # Seperator can be anything, including single space other than whitespace characters.
        if all(
            (
                " " not in sep_val,
                self._whitespace_checker(sep_val, show_msg=False),
            )
        ):
            KeyException(
                "[INVALID SEP-VALUE]\n"
                "The specified sep value contains whitespace characters (excluding single space). "
                "Such characters are prohibited in this context and will be filtered out.",
                log_method=logger.error,
            )

        # Return the processed separator value, including a single space
        return self._filter_chars(sep_val, include_chars=" ")

    def _wrap_text(self, text: str) -> str:
        """
        Wrap only text with ASCII letters and digits.
        
        #### NOTE::
        
        - Wraping text with punctuation characters (other than the seperator) is not implemented in this program.
        - This program is primarily designed to support separators with standard characters only when wrapping text.
        - If you require custom separators, please refrain from using special characters, and consider using standard characters \
            such as ASCII letters and digits (default) with separators.
        """
        if self._use_words:
            return text

        # Check for special characters in the text
        if all(
            (
                not self._include_all,  # Skip if all characters are included
                self._punctuation_checker(
                    self._filter_chars(text, exclude_chars=self._sep)
                ),
            )
        ):
            raise KeyException(
                "[SPECIAL CHARACTERS DETECTED]\n"
                "This program is primarily designed to support separators with standard characters only. "
                "To avoid potential issues, refrain from using parameters that may contain or result in special characters."
                "\nParameters: ('seperators', 'sep-width', 'include_all_chars', 'exclude_chars')\n"
                "If seperators required, consider using standard characters such as ascii_letters and digits (default).",
            )

        int_instance = lambda x: isinstance(x, int)
        len_text = len(text)
        invalid_width_str = "[INVALID WIDTH-INDEX]\n"

        # Check if the width is an integer or an Iterable
        if self._width:
            self._obj_instance(self._width, obj_type=(int, Iterable))

        if not self._width or int_instance(self._width):
            width = 4 if not self._width else self._width

            # Check for separator width and key length compatibility
            if len_text != 1 and width >= len_text:
                if abs(operator.sub(len_text, width)) <= 1:
                    width -= 1
                    KeyException(
                        "[SEP-WIDTH ADJUSTMENT]\n"
                        "The specified 'width' value is larger than the length of the text. "
                        "The width value will be adjusted to ensure compatibility with the text length. "
                        f"\n>>> {width = }"
                        f"\n>>> {len_text = }",
                        log_method=logger.warning,
                    )
                else:
                    raise KeyException(
                        "[INVALID SEP-WIDTH]\n"
                        "The provided 'width' value must be 1 less than the specified key length or the length of the conjoined words. "
                        "This requirement ensures that the separator is not automatically excluded, mitigating unintended behavior."
                        f"\n>>> {width = }"
                        f"\n>>> {len_text = }",
                        log_method=logger.error,
                    )
            # Wrap the text using the specified separator
            sep_key = self._sep.join(textwrap.wrap(text=text, width=width))
            return sep_key
        elif self._width and isinstance(self._width, Iterable):
            # Validate the index values to ensure they are integers and greater than 0
            if not all(map(lambda x: int_instance(x) and x >= 0, self._width)):
                raise KeyException(
                    f"{invalid_width_str}"
                    "The specified width index values must be integers and greater than 0. "
                    "Please specify valid index values within the range of the key length provided."
                    f"\n>>> {self._width = }",
                    log_method=logger.error,
                )
            # Sort the index values in ascending order.
            # This ensures that the separator is placed at the specified index values.
            # If the last index value is greater than the length of the text, raise an exception.
            width = sorted(self._width)
            if last_width_item := width[-1] > len_text:
                raise KeyException(
                    f"{invalid_width_str}"
                    "The specified width index value exceeds the length of the text. "
                    "Please specify a valid index value within the range of the text length."
                    f"\n>>> {last_width_item = }",
                    log_method=logger.error,
                )

            t = ""
            for idx, s in enumerate(text):
                if (idx == 0 and 0 in self._width) or idx in width:
                    # If the index value is found in the specified width,
                    # the separator will be placed at the specified index value.
                    t += self._sep + s
                else:
                    # Otherwise, the next character will be appended to the key.
                    t += s
            return t

    def _generate_keys(self) -> NamedTuple:
        num_keys = (
            5
            if not self._num_of_keys
            else self._length_checker(self._num_of_keys, obj="num_of_keys")
        )

        def key_generator():
            return KeyCraftsman(
                key_length=self._key_length,
                exclude_chars=self._exclude_chars,
                include_all_chars=self._include_all,
                unique_chars=self._unique_chars,
                bypass_unique_limit=self._bypass_unique,
                encoded=self._encoded,
                urlsafe_encoded=self._urlsafe,
                num_of_keys=self._num_of_keys,
                num_of_words=self._num_of_words,
                sep=self._sep,
                sep_width=self._width,
                keyfile_name=self._kfile_name,
                use_words=self._use_words,
                overwrite_keyfile=self._overwrite,
                verbose=not logger.disabled,  # If the logger is disabled, the verbose parameter will be False.
            ).key

        keys_gen = (
            self._EXECUTOR().submit(key_generator) for _ in range(1, num_keys + 1)
        )
        key_results = iter(tee(k.result() for k in as_completed(keys_gen)))

        # Return the generated keys as a namedtuple
        return self._keytuple(*next(key_results))

    def _keytuple(self, *args: Any) -> NamedTuple:
        """`Keys(namedtuple)` containing the generated key(s)."""
        Keys = namedtuple(
            typename="Keys",
            field_names=(
                field_names := tuple(f"key{i}" for i in range(1, len(args) + 1))
            ),
            module=(cls_name := self.__class__.__name__),
            defaults=[None] * len(field_names),
        )
        Keys.__doc__ = (
            f"A {cls_name!r} namedtuple instance containing the generated key(s)."
        )
        return Keys(*args)

    @classmethod
    def _filter_words(
        cls, dataset: Iterable, break_point: int = 0, unique: bool = False
    ) -> set:
        """
        Filter the generated words based on the specified parameters.

        #### Parameters:
            - `dataset` (Iterable): The dataset from which the words are generated.
            - `break_point` (int): The number of words to generate.
            - `unique` (bool): Whether to generate unique words.

        #### Returns:
            - `set`: The filtered set of words based on the specified parameters.

        #### Notes:
            - This method filters the generated words based on the specified parameters.
            - If the `unique` parameter is enabled, the method will check if the generated words are unique.
            - If the `unique` parameter is disabled, the method will return the filtered set of words.
            - The method will recursively check if the generated words are unique and re-generate the words if necessary.

        """
        words_set = set()
        for w in dataset:
            while len(words_set) != break_point:
                if unique:
                    # If the 'unique_chars' parameter is enabled, check if the word contains unique characters.
                    if all(map(lambda x: x == 1, Counter(w).values())):
                        # If the word contains unique characters, add it to the set.
                        words_set.add(w)
                else:
                    words_set.add(w)
                break

        # Validate the uniqueness of the generated word(s).
        if unique:
            is_unique = cls.unique_test(words_set, test_only=True)
            if is_unique:
                KeyException(
                    "[UNIQUE-WORDS VALIDATED]\n"
                    "Validation check for unique words passed. "
                    "The generated word(s) appear(s) to be unique and does not require to be re-generated."
                    f"\n>>> {is_unique = }",
                    log_method=logger.debug,
                )
            else:
                KeyException(
                    "[RE-GENERATING UNIQUE WORD(s)]\n"
                    "The generated word(s) are not unique and will be re-generated based on the specified parameters."
                    f"\n>>> {is_unique = }",
                )
                # If the generated word(s) are not unique,
                # re-generate the word(s) based on the filtered set of characters.
                return cls._filter_words(
                    dataset=dataset, break_point=break_point, unique=unique
                )
        return words_set

    def _generate_words(self):
        self._length_checker(self._num_of_words)
        self._obj_instance(self._num_of_words, obj_type=int)
        with open(Path(__file__).parent / "all_words.json") as words_file:
            # Load all hardcoded words from the json file.
            w_file = json.load(words_file)
        total_words, all_words = (
            w_file.pop(k) for k in ("Total Unique-Words", "WORDS")
        )

        # Generate a random sample of words from the specified population.
        random_words = self._randomify(
            population=all_words, k=max(self._num_of_words, total_words)
        )
        words_set = self._filter_words(
            dataset=random_words,
            unique=self._unique_chars,
            break_point=self._num_of_words,
        )

        if self._width:
            # If the 'width' parameter is specified, wrap the words based on the specified width.
            if not isinstance(self._width, int) or isinstance(self._width, Iterable):
                raise KeyException(
                    "[INVALID SEP-WIDTH]\n"
                    "The specified width value must be a positive integer in this context."
                    f"\n>>> {self._width = }",
                    log_method=logger.error,
                )
            sep_word_set = self._sep.join(words_set)
            words_set = textwrap.wrap(text=sep_word_set, width=self._width)
        # Return the generated word(s) as a string separated by the specified separator.
        return self._sep.join(words_set)

    @staticmethod
    def _randomify(**kwargs) -> list[str]:
        """
        Generate a random sample of a given population.

        #### Parameters:
            - `population` (str): The population from which to generate the random sample.
            - `k` (int): The number of elements to sample from the population.

        #### Returns:
            - `list`: The random sample generated from the specified population.

        #### Notes:
            - This method uses the `random.SystemRandom().sample` method to generate a random sample
            from the specified population.
            - The sample size is determined by the value of the `k` parameter.
        """
        return SystemRandom().sample(**kwargs)

    def _generate_key(self) -> Union[bytes, str]:
        KExceptionInfo = partial(
            KeyException, log_method=logger.info, disable_color=True
        )
        KExceptionInfo(
            "[KEY-GENERATION PROCESS STARTED]\n"
            "Depending on the specified parameters and the system's specifications, this process may take some time."
        )

        if self._use_words:
            return self._generate_words()

        key_length = self._length_checker(self._key_length)
        slicer = lambda *args: "".join(islice(*args, self._check_scale(key_length)))
        all_chars = slicer(cycle(self._ALL_CHARS))

        KExceptionInfo(
            "[CHARACTER-SET FILTERING STARTED]\n"
            "Filtering the character set based on the specified parameters. "
            "This process ensures that the generated key(s) adhere to the specified constraints."
        )

        # If no characters are specified for exclusion, the character set will be filtered based on the punctuation characters.
        filtered_chars = self._filter_chars(all_chars, exclude_chars=punctuation)

        if self._include_all:
            # If all characters are to be included, the character set will not be filtered.
            filtered_chars = all_chars
        elif self._exclude_chars:
            self._obj_instance(self._exclude_chars, obj_type=(int, str))
            filter_char = partial(self._filter_chars, all_chars)
            exclude_chars_type = self.char_excluder(self._exclude_chars)
            # ** Characters are excluded from the character chartset if found based on key name or index value.
            # ** Otherwise, punctuation characters will be filtered if no single characters are specified for exclusion.
            if exclude_chars_type:
                # If the specified key is found in the exclusion chart, the corresponding character set will be filtered.
                filtered_chars = filter_char(exclude_chars=exclude_chars_type)
            else:
                # If the specified key is not found in the exclusion chart
                # the specified characters will be filtered.
                KeyException(
                    "[EXCLUSION-CHART INVALID OPTION]\n"
                    "If intended, the specified exclusion option was not found in the exclusion chart. "
                    "Otherwise, the character set will be filtered based on the specified characters.",
                    log_method=logger.warning,
                )
                filtered_chars = filter_char(exclude_chars=self._exclude_chars)

        generated_key: list = self._randomify(
            population=filtered_chars, k=min(key_length, len(filtered_chars))
        )

        if self._unique_chars:
            KExceptionInfo(
                "[UNIQUE-CHARS VALIDATION-CHECK STARTED]\n"
                "Checking if the generated key(s) are unique based on the specified parameters."
            )
            is_unique = self.unique_test(generated_key, test_only=True)
            too_large = key_length > (unique_chars_len := len(set(filtered_chars)))
            if is_unique:
                # Skips if set of characters are all unique.
                KeyException(
                    "[UNIQUE-CHARS VALIDATED]\n"
                    "The generated key(s) already appear(s) to be unique and will not be re-generated.",
                    log_method=logger.debug,
                )
            else:
                KeyException(
                    "[RE-GENERATING UNIQUE KEY(s)]\n"
                    "The generated key(s) are not unique and will be re-generated based on the filtered set of characters. "
                    "Re-generating the key(s) based on the filtered set of characters. "
                    "While ensuring the key length is less than or equal to the length of the filtered unique char set.",
                    log_method=logger.warning,
                )

                if all((self._bypass_unique, too_large)) and any(
                    (
                        self._exclude_chars in self._UNIQUE_DISABLED,
                        len(generated_key) in self._UNIQUE_DISABLED.values(),
                    )
                ):
                    # XXX Unique Chars Disabled
                    # This overrides the limited fixed lengths
                    # for ('oct_ascii_punct', 'ascii_punct') after set filtering.
                    KeyException(
                        "[UNIQUE-CHARS DISABLED]\n"
                        "Please be advised that the 'unique_chars' parameter has been disabled. "
                        "Using ('oct_ascii_punct' (size=2), 'ascii_punct' (size=10)) exclusion options may result in unsecure key lengths "
                        "when the 'unique_chars' parameter is enabled.",
                        log_method=logger.warning,
                    )
                    self._unique_chars = False
                else:
                    invalid_klen_str = "[KEY-LENGTH VALIDATION]\n"
                    if not self._bypass_unique:
                        bypass_ulimit_str = "\nConsider using the 'bypass_unique_limit' parameter to bypass the unique maximum limit."
                        if too_large:
                            # Skips if specified key length is greater than the length of the filtered set of characters.
                            raise KeyException(
                                f"{invalid_klen_str}"
                                "Unable to generate a unique key with the specified parameters. "
                                "Key length must be less than or equal to the length of the filtered char set."
                                f"{bypass_ulimit_str}"
                                f"\n>>> {key_length = }"
                                f"\n>>> {unique_chars_len = }",
                                log_method=logger.error,
                            )
                        elif not too_large:
                            # Valid for unique set filtering.
                            # Skips if specified key length is less than or equal to the length of the filtered set of characters.
                            # Re-generates the key based on the filtered set of characters.
                            gen_set = set(all_chars) & set(filtered_chars)
                            generated_key = self._randomify(
                                population=tuple(gen_set),
                                k=min(key_length, len(all_chars)),
                            )
                        else:
                            raise KeyException(
                                f"{invalid_klen_str}"
                                "In order to use 'unique_chars' parameter, the key length must be less than "
                                "or equal to the length of all or filtered set of characters."
                                f"{bypass_ulimit_str}",
                                log_method=logger.error,
                            )
        KExceptionInfo(
            "[KEY-GENERATION PROCESS ENDED]\n"
            "The key generation process has been successfully completed."
            "\nThe generated key(s) can be accessed using the 'key' or 'keys' property."
        )
        return "".join(generated_key)[:key_length]

    @classmethod
    def encode_key(cls, key: str, urlsafe_encoded: bool = False) -> bytes:
        """
        Encode the generated key using the specified encoding method.

        #### Parameters:
            - `key` (str): The generated key to be encoded.
            - `urlsafe_encoded` (bool): Whether to encode the key using the URL-safe encoding method.

        #### Returns:
            - `bytes`: The encoded key based on the specified encoding method.

        #### Raises:
            - `KeyException`:
                - If the key is not of type `str`.
        """
        cls._obj_instance(key, obj_type=str)
        return [encoded_key := key.encode(), cls._base64_key(encoded_key)][
            bool(urlsafe_encoded)
        ]

    @cached_property
    def key(self) -> Union[bytes, str]:
        if self._key is None:
            self._key = self._generate_key()
            # TODO: Create a Text Wrapping class?
            if self._wrap_key:
                self._key = self._wrap_text(text=self._key)
            if self._encode_key:
                self._key = self.encode_key(self._key, urlsafe_encoded=self._urlsafe)
        return self._key

    @cached_property
    def keys(self) -> NamedTuple:
        if self._keys is None:
            self._keys = self._generate_keys()
        return self._keys

    @classmethod
    def file_exists(cls, file: Path, change_file: bool = False) -> Union[bool, Path]:
        """
        Check if the specified file exists.

        #### Parameters:
            - `file` (Path): The file to be checked for existence.
            - `change_file` (bool): Whether to change the file name if the file already exists.

        #### Returns:
            - `Union[bool, Path]`:
                - If `change_file` is False, the method will return a boolean value indicating whether the file exists.
                - If `change_file` is True:
                    - The method will trail the file name with a unique set of digits recursively until the file name is unique.

        #### Raises:
            - `KeyException`: Raised if the specified file is not of type `Path`.
        """

        file = cls._obj_instance(file, obj_type=Path)
        if not change_file:
            # Only checks if the file exists.
            return cls._check_combos(
                (file.is_file(), file.is_absolute()), check_only=True
            )

        fp_name = file.stem
        ext = file.suffix  # (".bin" or ".json")

        def make_it_unique(unique_file):
            if not cls.file_exists(unique_file):
                return unique_file
            else:
                # Trail file name using a unique set of digits using `random.SystemRandom()`
                # to ensure the file name is unique.
                unique_id = "".join(set(cls._randomify(population=digits, k=10)))
                trail_id = "ID" + unique_id[:5]
                unique_file = unique_file.with_name(
                    f"{fp_name}_{trail_id}"
                ).with_suffix(ext)

                # Recursively call the function to check if the file exists.
                return make_it_unique(unique_file)

        return make_it_unique(file)

    @cache
    def _get_filename(
        self, default_name: str = "generated_key", ext: str = "bin"
    ) -> Path:
        fp_name = (
            self._obj_instance(self._kfile_name, obj_type=(Path, str)) or default_name
        )
        if isinstance(fp_name, str):
            fp_name = Path(fp_name).stem
        ext = "." + ext
        file = (Path.cwd() / fp_name).with_suffix(ext)
        file_found = self.file_exists(file)
        if not self._overwrite and file_found:
            # Default file name: 'generated_key_ID<int>.<bin/json>'
            # File name will recursively change if the file already exists
            # and the 'overwrite_keyfile' parameter is False.
            file = self.file_exists(file, change_file=True)
        else:
            if file_found:
                KeyException(
                    "[OVERWRITING-KEYFILE]\n"
                    "Key file found and already exists. "
                    "Overwriting file with new key(s) based on the specified parameters.",
                    log_method=logger.warning,
                )
        return file

    @staticmethod
    def _export_message(fp: Path) -> None:
        KeyException(
            f"\033[34m{fp.resolve().as_posix()!r}\033[0m has successfully been exported.",
            log_method=logger.info,
        )

    def export_key(self) -> None:
        """
        Export the generated key to a text (`.bin`) file.

        - NOTE::

        - If the generated key(s) ar

        """
        fp = self._get_filename()
        with open(fp, mode="w") as key_file:
            key_file.write(str(self.key))
        self._export_message(fp)

    def export_keys(self) -> None:
        """
        Export the generated keys to a JSON file.

        #### Raises:
            - `KeyException`: Raised for errors during file export, such as any of the following:
                - JSON encoding issues.
                - URLSafe encoded keys are present.
                    #### NOTE::

                    [JSON SERIALIZATION]
                        - Encoded keys (`.encode()`) will be decoded (`.decode()`).
                        - URLSafe-Encoded keys will be converted as string values.
        """

        fp = self._get_filename(default_name="generated_keys", ext="json")
        keys = self.keys._asdict()

        def dump_file(data):
            with open(fp, mode="w") as keys_file:
                json.dump(data, keys_file, indent=4)

        try:
            # Attempts to serialize keys as JSON.
            dump_file(keys)
        except json.JSONDecodeError as json_error:
            raise KeyException(
                "[JSON-DECODING]"
                f"\nError occurred while encoding the data to JSON: {json_error}."
                "\nPlease ensure that the data is properly formatted for JSON encoding."
            )
        except TypeError:
            # Outputs an exception if encoded/urlsafe-encoded keys are present.
            KeyException(
                "[JSON-SERIALIZATION FAILED]"
                "\nIf encoded/urlsafe-encoded key(s) are present, "
                "all keys will be serialized for compatibility.",
                log_method=logger.warning,
            )

            if self._encode_key:
                # Serialize for JSON format.
                keys = {k: str(v) for k, v in keys.items()}

            dump_file(keys)

        except Exception as e_error:
            raise KeyException(
                "An error has occured during the exportation of keys."
                f"Original Exception:"
                f"\n{type(e_error).__name__}: {str(e_error)}"
            )
        finally:
            # Outputs a message indicating successful completion of the export process.
            self._export_message(fp)


def excluder_chart(
    format_type: Literal["dict"] = None, include_index: bool = False, **kwargs
) -> Union[dict[str, str], str, None]:
    """
    This function returns a dictionary containing all possible exclude types for the `exlude_chars` parameter.

    #### Parameters:
        - `format_type` (Literal["dict"], optional): The format type for the returned dictionary.
            - If 'dict', the function will return a dictionary containing all possible exclude types.
            - If None, the function will print the exclusions chart by default.
        - `include_index` (bool, optional): If True, the function will return a dictionary containing all possible exclude types with its index value.
        - `**kwarg`: Additional keyword arguments to be passed to the `KeyCraftsman.print_echart` method.
            - `fp` (Path | str): The file path to export the exclusions chart.
            - `return_table` (bool): If True, the function will return the exclusions chart as a string.
            - `**kwargs`: Additional keyword arguments to be passed to the `PrettyTable.get_string()` method.

    #### Important Notes:
        - The keys in the dictionary represent the possible exclude types.
        - The values in the dictionary represent the character sets to be excluded from the generated key.
        - The character sets are based on the ASCII letters, digits, and punctuation characters.
        - Whitespace characters ((space)\\t\\n\\r\\v\\f) are automatically excluded from the charset.
    """
    if format_type == "dict" or include_index:
        return KeyCraftsman.char_excluder(
            return_chart=not include_index, include_index=include_index
        )
    return KeyCraftsman.print_echart(**kwargs)


def generate_secure_keys(
    num_of_keys: int = 2, keyfile_name: str = "", overwrite_keyfile: bool = False
) -> Union[bytes, NamedTuple]:
    """
    Generate secure cryptographic key(s) using the `KeyCraftsman` class with customizable parameters.

    #### Parameters:
        - `num_of_keys` (int): Number of keys to generate. Defaults to 2.
        - `keyfile_name` (str): Name of the file when exporting the key.
        - `overwrite_keyfile` (bool): If True, overwrite the key file if it already exists. Defaults to False.

    #### Returns:
        - `bytes`: The generated cryptographic key.
        - `NamedTuple`[bytes]: A NamedTuple containing multiple generated cryptographic keys.

    #### NOTE::

        - This function is designed to facilitate the generation of secure cryptographic keys with customizable parameters.
            - The following parameters are hardcoded to ensure high security and compatibility with various cryptographic libraries:
                - `key_length`: 32
                - `urlsafe_encoded`: True
                - `include_all_chars`: True
                - `unique_chars`: True

    """
    secure_key = KeyCraftsman(
        key_length=32,
        urlsafe_encoded=True,
        unique_chars=True,
        include_all_chars=True,
        num_of_keys=num_of_keys,
        keyfile_name=keyfile_name,
        overwrite_keyfile=overwrite_keyfile,
    )
    method = partial(_get_method, secure_key, status=num_of_keys)
    if any((keyfile_name, overwrite_keyfile)):
        method(attr="export_key")
    return method(attr="key")


def _get_method(
    obj: KeyCraftsman, attr: Literal["key", "export"] = "key", status: bool = False
) -> Any:
    """
    Retrieve a method or attribute from the KeyCraftsman object based on the provided parameters.

    #### Parameters:
        - `obj` (KeyCraftsman): The KeyCraftsman object from which to retrieve the method or attribute.
        - `attr` (Literal["key", "export"]): The desired attribute or method, either 'key' or 'export'.
        - `status` (bool, optional): If True, appends 's' to the attribute if it represents a method.
            Defaults to False.

    #### Returns:
        - `Any`: The requested method or attribute from the KeyCraftsman object.
            - If status is True, the method will return the attribute with an appended 's'.
            - If the attribute is 'export', the method will be executed to export the key(s) to a file.
            - If the attribute is 'key', the method will be executed to retrieve the generated key(s).

    #### NOTE::

        - Facilitating flexible access to generating and exporting keys from the KeyCraftsman object.
    """
    attr_method = getattr(obj, attr + "s" if status else attr)
    if attr == "export_key":
        attr_method()
    return attr_method


def simple_pwd(
    multiple_keys: bool = False, keyfile_name: str = "", sep: str = "-"
) -> Union[NamedTuple, str]:
    """
    Generate a simple unqiue password using the `KeyCraftsman` class with quick parameters.

    #### Parameters:
        - `multiple_keys` (bool): Generate multiple keys with a single instance. Defaults to False.
        - `keyfile_name` (str): Name of the file when exporting the key. Defaults to an empty string.
        - `sep` (str): The specified separator for text wrapping. Defaults to a hyphen (-).

    #### Returns:
        - `Any`: The generated passkey or cryptographic key(s).
            - `str`: The generated passkey.
            - `NamedTuple`[bytes]: A NamedTuple containing multiple generated cryptographic keys.
        - If `keyfile_name` is specified, the generated key(s) will be exported to a file before being returned.

    #### NOTE::

        - This function is designed to facilitate the generation of simple passwords with minimal parameters.
    """
    pwd = KeyCraftsman(keyfile_name=keyfile_name, sep=sep, unique_chars=True)
    method = partial(_get_method, pwd, status=multiple_keys)
    if keyfile_name:
        method(attr="export_key")
    return method(attr="key")


def kc_uuid(version: Literal[1, 2, 3, 4, 5] = None) -> uuid.UUID:
    """
    Generate a UUID using the `KeyCraftsman` class.

    #### Parameters:
        - `version` (Literal[1, 2, 3, 4, 5], optional): The version number for the UUID.

    #### Returns:
        - `UUID`: A universally unique identifier (UUID) generated using the `KeyCraftsman` class.

    #### NOTE::

            - This function is designed to facilitate the generation of universally unique identifiers (UUIDs).
            - The UUID is first generated using the `KeyCraftsman` class and then converted to a UUID object.

    #### UUID Versions
        `Version 1`: Time-based UUID. Generated based on the current timestamp and the unique identifier of the machine (MAC address).
        `Version 2`: DCE Security UUID. Similar to version 1 but includes POSIX UID/GID.
        `Version 3`: MD5 hash-based UUID. Generated based on a namespace identifier and a name.
        `Version 4`: Random UUID. Generated using a random or pseudo-random number.
        `Version 5`: SHA-1 hash-based UUID. Similar to version 3 but uses the SHA-1 hash algorithm.

    """
    # Using index values (8, 12, 16, 20) for the separator width.
    # This ensures that the separator is placed at the corect RFC 4122 UUID positions.
    kc = KeyCraftsman(
        key_length=32, sep="-", sep_width=(8, 12, 16, 20), exclude_chars="non_rfc_4122"
    )

    if version:
        KeyCraftsman._obj_instance(version, obj_type=int)
        if version not in (version_defaults := tuple(range(1, 6))):
            raise KeyException(
                "[INVALID UUID-VERSION]\n"
                "The specified UUID version number is invalid and considered illegal."
                f"\n>>> {version_defaults = }"
                f"\n>>> Received -> {version = }"
            )
    return uuid.UUID(kc.key, version=version)


# XXX Metadata Information
METADATA = {
    "version": (__version__ := "1.2.11"),
    "license": (__license__ := "Apache License, Version 2.0"),
    "url": (__url__ := "https://github.com/yousefabuz17/KeyCraftsman"),
    "author": (__author__ := "Yousef Abuzahrieh <yousef.zahrieh17@gmail.com"),
    "copyright": (__copyright__ := f"Copyright © 2024, {__author__}"),
    "summary": (
        __summary__ := "A modern Python class for generating secure and customizable keys."
    ),
    "doc": (__doc__ := KeyCraftsman.__doc__),
}


if __name__ == "__main__":
    print(repr(KeyCraftsman()))


__all__ = (
    "METADATA",
    "_get_method",
    "KeyCraftsman",
    "KeyException",
    "excluder_chart",
    "generate_secure_keys",
    "simple_pwd",
    "kc_uuid",
)
