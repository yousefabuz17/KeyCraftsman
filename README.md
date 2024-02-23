<img src="logo/key-craftsman-logo.jpg" alt="KeyCraftsman Logo" width=200>

# KeyCraftsman
[![PyPI version](https://badge.fury.io/py/dynamic-loader.svg)](https://badge.fury.io/py/key-craftsman)
[![Downloads](https://pepy.tech/badge/dynamic-loader)](https://pepy.tech/project/key-craftsman)
[![License](https://img.shields.io/badge/license-Apache-blue.svg)](https://opensource.org/license/apache-2-0/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://github.com/yousefabuz17/KeyCraftsman/blob/main/README.md)
[![Code Style](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)


# KeyCraftsman

`KeyCraftsman` is a modernized Python class designed to generate secure and customizable keys. It offers features such as specifying key length, excluding characters, including all characters, URL-safe encoding, and more. The generated key can be exported to a file for future use.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Parameters](#parameters)
- [Attributes](#attributes)
- [Methods](#methods)
- [Raises](#raises)
- [Usage Examples](#usage-examples)
- [Feedback](#feedback)
  - [Contact Information](#contact-information)
- [License](#license)
---

## Installation:

```bash
pip install key-craftsman
```

---
## Features:

- **Key Generation**: Generate secure and customizable keys with various parameters.
- **Key Length**: Specify the length of the generated keys.
- **Exclude Characters**: Exclude specific characters from the generated keys.
- **Include All Characters**: Include all ASCII letters, digits, and punctuation in the generated keys.
- **Unique Characters**: Ensure that the generated key(s) or word(s) contain unique characters.
- **URL-Safe Encoding**: Utilize URL-safe base64 encoding for generated keys.
- **Export Key(s)**: Export the generated key(s) to a file with optional formatting.
- **Custom Text Wrapping**: Wrap the generated key with a custom separator and width.
- **Multiple Key Generation**: Generate multiple keys with a single instance.
- **Word Generation**: Generate words using the `random.SystemRandom()` method.
- **Verbose Mode**: Enable or disable verbose mode for logging and printing exceptions.
- **Custom Key File Name**: Specify a custom name for the exported key file.
- **Overwrite Key File**: Overwrite the key file if it already exists.
- **Exclusion Chart**: Print and export the exclusion chart for help in excluding characters.
- **RFC 4122 Compliant UUID**: Generate an RFC 4122 compliant UUID using the `kc_uuid` function.
---


## Parameters:

- `key_length` (`int`): The length of the generated key. Defaults to 32.
  - The key length must be a positive integer.
  - The maximum capacity is determined by the system's maximum integer size.
- `exclude_chars` (`Union[int, str]`): Characters to exclude from the generated key.
  - If not specified, only punctuation characters will be excluded.
  - Please refer to the `char_excluder()` method for all possible exclude types.
  - Whitespace characters are automatically excluded from the charset.
  - The input can be a string key type or index value from the exclusion chart.
  - `Examples`:
    - Excluding specific characters:
      - `exclude_chars="punct"` will exclude punctuation characters from the generated key.
      - `exclude_chars="octo_ascii_upper_punct"` will exclude octal digits, uppercase ASCII letters, and punctuation characters.
      - `exclude_chars=1` will exclude punctuation characters from the generated key.
      - `exclude_chars=29` will exclude octal digits, uppercase ASCII letters, and punctuation characters.
- `include_all_chars` (`bool`): Whether to include all characters (ASCII letters, digits, and punctuation).
- `unique_chars` (`bool`): Whether to ensure that the generated key contains unique characters.
  - This feature is useful for generating unique keys for specific use cases.
  - If the key length is larger than the length of the unique character set, an exception will be raised.
  - If the generated key is already unique, a warning message will be printed in verbose mode.
  - If the unique character limit is bypassed, a warning message will be printed in verbose mode.
- `bypass_unique_limit` (`bool`): Whether to bypass the unique character limit.
- `encoded` (`bool`): Whether to encode the generated key(s).
- `urlsafe_encoded` (`bool`): Whether to use URL-safe base64 encoding. Defaults to False.
  - If True, the generated key will be encoded using URL-safe base64 encoding (`base64.urlsafe_b64encode`).
- `num_of_keys` (`int`): Number of keys to generate when using `export_keys()`.
  - If not specified, the default number of keys is 2.
  - The maximum number of keys is determined by the system's maximum integer size.
- `use_words` (`bool`): Whether to use words for key generation.
  - `num_of_words` (`int`): Number of words to generate using `random.SystemRandom()`.
    #### NOTE::

    - `num_of_words` parameter will be ignored if `use_words` is disabled.

- `sep` (`str`): The specified separator for text wrapping.
  - If not specified, the key will not be wrapped with a separator.
  - It is recommended to use one character of any standard characters for the separator (e.g., ascii_letters, digits).
  - The length of the separator must be 1 unless using `use_words`.
  - `sep_width` (`Union[int, Iterable]`): Width for text wrapping when using separators.
    - If not specified:
      - The default width is 4 if using keys and not words.
      - The default width is the length of the word divided by 2 if using words.
    - The width is only applicable when using separators.
    - The width must be 1 less than the key length to prevent the separator from being excluded.
    - XXX Examples:
      - `sep=":"` will wrap the generated key with a colon separator.
      - `sep_width=4` will wrap the generated key with a colon separator and a width of 4.
      - `sep_width=(1, 5, 7)` will wrap the generated key with a colon separator at indexes 1, 5, and 7.
- `keyfile_name` (`str`): Name of the file when exporting key(s).
  - If not specified, a default file name will be used.
  - The default file name is 'generated_key(s)'.
  - The file extension will be '.bin' for single keys and '.json' for multiple keys.
  - If the file exists and:
    - `overwrite_keyfile` is False, a unique file name will be generated.
      - 'generated_key(s)_ID<int>.bin' or 'generated_key(s)_ID<int>.json'
    - `overwrite_keyfile` is True, the existing file will be overwritten.
- `overwrite_keyfile` (`bool`): Whether to overwrite the key file if it already exists.
  - If False, a unique file name will be generated to avoid overwriting the existing file.
  - If True, the existing file will be overwritten with the new key(s).
- `verbose` (`bool`): Whether to enable verbose mode for printing exceptions.
  #### NOTE::

  - Messages will only be printed to the console but not be logged to a file.
  - The logger is intended for stream handling only.
---


## Attributes:

- `key`: Cached property to retrieve a single generated key.
- `keys`: Cached property to retrieve a dictionary of multiple generated keys.
- `_ALL_CHARS`: Class attribute containing all ASCII letters, digits, and punctuation.
- `_MIN_CAPACITY`: Class attribute defining the minimum key capacity (Value: 100_000)
- `_MAX_CAPACITY`: Class attribute defining the maximum key capacity (Value: 9_223_372_036_854_775_807)
- `_EXECUTOR`: Class attribute for the ThreadPoolExecutor.
---


## Methods:

- `export_key()`: Exports the generated key to a file.
- `export_keys()`: Exports multiple generated keys to a JSON file.
- `print_echart()`: Print and export the exclusion chart for help in excluding characters.
---


## Raises:

- `(V)` (Verbose Mode Enabled): Will not raise, but messages will be printed to the console.
- `StopIteration`: When the class is iterated over and the number of keys is reached.
- `KeyException`: When encountering issues during key generation or exportation.
  - If any of the parameter types are invalid:
    - Positive Integer (`int`):
      - `key_length` # Must be less than the maximum capacity.
      - `num_of_keys`
      - `num_of_words` # Must be less than the maximum capacity.
    - String (`str`):
      - `sep` # Must be a single character.
      - `keyfile_name`
    - Boolean (`bool`):
      - `unique_chars`
      - `bypass_unique_limit`
      - `include_all_chars`
      - `encoded`
      - `urlsafe_encoded`
      - `use_words`
      - `overwrite_keyfile`
      - `verbose`
      #### NOTE::
      - Messages will only be printed to the console but not be logged to a file.
      - The logger is intended for stream handling only.
    
    - Union[`int`, `str`]:
      - `exclude_chars` # Example: "punct" or 1
    - Iterable (Union[`int` | `str`, `Iterable`]):
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
  - (V) When the specified separator contains prohibited whitespace characters (excluding single space).
  - (V) When special characters are detected in the text when wrapping.
  - (V) When `unique_chars` is enabled and the generated key is already unique.
  - (V) When attempting to serialize the generated keys to a JSON file.
  - (V) When the default or specified key file already exists and `overwrite_keyfile` is False.
  - (V) When exporting the generated key(s) to a file.
---


## Usage Examples:

```python
# Generate encoded or URLSafe-encoded keys.
key_gen = KeyCraftsman(key_length=32, num_of_keys=2, include_all_chars=False, encoded=True)

key = key_gen.key  # Retrieve a single encoded generated key.
keys = key_gen.keys  # Retrieve a dictionary of multiple encoded generated keys from the same instance.

key_gen.export_key()  # Export the generated key to a file.
key_gen.export_keys()  # Export multiple generated keys to a JSON file.

# Class can be iterated over the key(s) depending on if the parameter 'num_of_keys' is passed in.
for k in key_gen:
    print(k)  # If 'num_of_keys' is not passed in, the class will iterate over the generated key.
    # If 'num_of_keys' is passed in, the class will iterate over the dictionary values of the generated keys.
    # Alternatively, the class can be iterated over using the `__next__` method.
    print(next(key_gen))

# Print the class object and export the exclusion chart for help in excluding characters.
print(key_gen)
print(key_gen.print_echart(return_table=True))  # PrettyTable object of the Exclusions Chart.
print(key_gen.print_echart(fp="exclusions_chart.txt"))  # Exclusions Chart exported to 'exclusions_chart.txt'.

# Custom text wrapping with a separator.
key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=4)
key = key_gen.key  # Retrieve a single generated key.

# Custom text wrapping with a separator and encoding.
key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=4, encoded=True)
key = key_gen.key  # Retrieve a single generated key.

# Custom text wrapping with a separator and URL-safe encoding.
key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=4, urlsafe_encoded=True)
key = key_gen.key  # Retrieve a single generated key.

# Generate words using with a custom separator.
key_gen = KeyCraftsman(num_of_words=2, sep="/", use_words=True)
word = key_gen.key  # Retrieve a single generated word.
keys = key_gen.keys  # Retrieve a dictionary of multiple generated words.

# Exclude specific characters from the generated key.
key_gen = KeyCraftsman(exclude_chars="abc#%()1")

# Exclude based on the exclusion chart option key or index value (e.g., 1-29).
key_gen = KeyCraftsman(exclude_chars="punct")
key_gen = KeyCraftsman(exclude_chars=1)

# Generate unique keys with a custom separator.
key_gen = KeyCraftsman(unique_chars=True)
key = key_gen.key  # Retrieve a single generated key.

# XXX If the key length is larger than the length of the unique character set, an exception will be raised.
  # If necessary, the unique character limit can be bypassed with the `bypass_unique_limit` parameter.


# Generate key(s) with an iterable separator width.
key_gen = KeyCraftsman(key_length=32, sep=":", sep_width=(1, 5, 7))
key = key_gen.key  # Retrieve a single generated key.
# Output: 'x:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx'

# Generate an RFC 4122 compliant key using the `kc_uuid` function with a custom version.
kc_id = kc_uuid(version: Literal[1,2,3,4,5] = None)
# Output: 'xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx'

# Generate secure keys with `generate_secure_keys` function.
secure_keys = generate_secure_keys(num_of_keys=5)
# Output: Keys(key1='...', key2='...', key3='...', key4='...', key5='...')

# Generate secure keys with `generate_secure_keys` function and export to a file.
generate_secure_keys(num_of_keys=5, keyfile_name="secure_keys")
# Output: Secure keys exported to 'secure_keys.json'.

```
---


# Feedback

Feedback is crucial for the improvement of the `DataLoader` project. If you encounter any issues, have suggestions, or want to share your experience, please consider the following channels:

1. **GitHub Issues**: Open an issue on the [GitHub repository](https://github.com/yousefabuz17/KeyCraftsman) to report bugs or suggest enhancements.

2. **Contact**: Reach out to the project maintainer via the following:

### Contact Information
- [Discord](https://discord.com/users/581590351165259793)
- [Gmail](yousefzahrieh17@gmail.com)

> *Your feedback and contributions play a significant role in making the `DataLoader` project more robust and valuable for the community. Thank you for being part of this endeavor!*

## License:

This project is licensed under the Apache 2.0 license. See the [LICENSE.md](LICENSE.md) file for details.