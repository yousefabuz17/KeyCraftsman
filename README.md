<img src="logo/key-craftsman-logo.jpg" alt="KeyCraftsman Logo" width=200>

# KeyCraftsman
[![PyPI version](https://badge.fury.io/py/key-craftsman.svg)](https://badge.fury.io/py/key-craftsman)
[![Downloads](https://static.pepy.tech/badge/key-craftsman)](https://pepy.tech/project/key-craftsman)
[![License](https://img.shields.io/badge/license-Apache-blue.svg)](https://opensource.org/license/apache-2-0/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://github.com/yousefabuz17/KeyCraftsman/blob/main/README.md)
[![Code Style](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)


# KeyCraftsman

`KeyCraftsman` is a modernized and innovative Python class designed to generate passcodes to your own liking. It offers features such as specifying key length, excluding characters, including all characters, URL-safe encoding, and more. The generated passkey(s) can be exported to a file for future use.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Parameters](#parameters)
- [Attributes](#attributes)
- [Methods](#methods)
- [Functions](#functions)
- [Raises](#raises)
- [Excluder Chart](#excluder-chart)
  - [Overview](#overview)
  - [How to Exclude Characters](#how-to-exclude-characters)
  - [Print and Export the Exclusion Chart](#print-and-export-the-exclusion-chart)
  - [Return the Exclusion Chart as a Dictionary](#return-the-exclusion-chart-as-a-dictionary)
  - [Whitespace Exclusion](#whitespace-exclusion)
- [Seperator](#seperator)
  - [Separator Examples](#separator-examples)
- [Iterating Over the Class](#iterating-over-the-class)
  - [Iteration Examples](#iteration-examples)
- [Unique Characters](#unique-characters)
  - [Limitations](#limitations)
  - [Bypass Unique Limit](#bypass-unique-limit)
- [Encoded and URL-Safe Encoded Keys](#encoded-and-url-safe-encoded-keys)
  - [Encoded and URL-Safe Encoded Examples](#encoded-and-url-safe-encoded-examples)
- [Obtain the Generated Key(s)](#obtain-the-generated-keys)
  - [Cached Properties](#cached-properties)
  - [Exporting the Generated Key(s)](#exporting-the-generated-keys)
  - [Usage Examples](#usage-examples)
- [Class Object Representation](#class-object-representation)
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

- **Passkey Generation**: Generate secure and customizable passkey(s) with various parameters.
- **Passkey Length**: Specify the length of the generated passkey(s).
- **Exclude Characters**: Exclude specific characters from the generated passkey(s).
- **Include All Characters**: Include all ASCII letters, digits, and punctuation in the generated passkey(s).
- **Unique Characters**: Ensure that the generated key(s) or word(s) contain unique characters.
- **URL-Safe Encoding**: Utilize URL-safe base64 encoding for generated passkey(s).
- **Export Passkey(s)**: Export the generated key(s) to a file with optional formatting.
- **Custom Text Wrapping**: Wrap the generated key with a custom separator and width.
- **Multiple Passkey Generation**: Generate multiple passkey(s) with a single instance.
- **Word Generation**: Generate words using the `random.SystemRandom()` method.
- **Verbose Mode**: Enable or disable verbose mode for logging and printing exceptions.
- **Custom Passkey File Name**: Specify a custom name for the exported key file.
- **Overwrite Passkey File**: Overwrite the key file if it already exists.
- **Exclusion Chart**: Print and export the exclusion chart for help in excluding characters.
- **RFC 4122 Compliant UUID**: Generate an RFC 4122 compliant UUID using the `kc_uuid` function.
---


## Parameters:

- `key_length` (`int`): The length of the generated key. Defaults to 16.
  - The key length must be a positive integer.
  - The maximum capacity is determined by the system's maximum integer size.
- `exclude_chars` (`Union[int, str]`): Characters to exclude from the generated key.
  - Please refer to [Excluder Chart](#excluder-chart) for more information.
- `include_all_chars` (`bool`): Whether to include all characters (ASCII letters, digits, and punctuation).
- `unique_chars` (`bool`): Whether to ensure that the generated key contains unique characters.
  - Please refer to [Unique Characters](#unique-characters) for more information.
- `bypass_unique_limit` (`bool`): Whether to bypass the unique character limit.
  - Please refer to [Bypass Unique Limit](#bypass-unique-limit) for more information.
- `encoded` (`bool`): Whether to encode the generated key(s).
- `urlsafe_encoded` (`bool`): Whether to use URL-safe base64 encoding. Defaults to False.
  - For more information on `encoded` and `urlsafe_encoded`, please refer to [Encoded and URL-Safe Encoded Keys](#encoded-and-url-safe-encoded-keys).
- `num_of_keys` (`int`): Number of keys to generate when using `export_keys()`.
  - If not specified, the default number of keys is 2.
  - The maximum number of keys is determined by the system's maximum integer size.
- `use_words` (`bool`): Whether to use words for key generation.
  - `num_of_words` (`int`): Number of words to generate using `random.SystemRandom()`.
    #### NOTE::

    - `num_of_words` parameter will be ignored if `use_words` is disabled.

- `sep` (`str`): The specified separator for text wrapping.
  - `sep_width` (`Union[int, Iterable]`): The width for text wrapping when using separators.
  - Please refer to [Seperator](#seperator) for more information.
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


## Functions:

- `kc_uuid()`: Generate a RFC 4122 compliant UUID.
- `generate_secure_keys()`: Generate urlsafe-encoded passkeys
- `excluder_chart()`: Print or export the exclusion chart for help in excluding characters.
- `simple_pwd()`: Generate a simple password containing only unique ASCII letters and digits with a hyphen as a separator.
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

## Excluder Chart
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                       Exclusions Chart (UD = Unique Disabled)                       │
├───────┬──────────────────────────┬──────────────────┬───────────────────────────────┤
│ Index │       Key-Options        │   Key-Samples    │ Unique Max Key-Size (Entropy) │
├───────┼──────────────────────────┼──────────────────┼───────────────────────────────┤
│   1   │          punct           │ 6ojX26KI2WP0Cs1D │           62 (5.95)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   2   │          ascii           │ |&8~+5%&:\3~`4%7 │           42 (5.39)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   3   │       ascii_lower        │ AGX(\^W%6,LA-~0B │           68 (6.09)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   4   │       ascii_upper        │ :k|ttbu7kxfc";27 │           68 (6.09)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   5   │     ascii_punct (UD)     │ q$\.Y@:.YY<~k>O% │           81 (6.34)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   6   │    ascii_lower_punct     │ 2CA8VUL45AYBGAGE │           36 (5.17)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   7   │    ascii_upper_punct     │ 1ib2q4k9jq3x03rs │           36 (5.17)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   8   │          digits          │ ]JC;p?pzd,TnI}Wl │           84 (6.39)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   9   │       digits_ascii       │ -|@]\(^~'`';%[<" │           32 (5.00)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   10  │       digits_punct       │ gYttMniucpVslWKc │           52 (5.70)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   11  │    digits_ascii_lower    │ LU:S(MK[VR(A\RC" │           58 (5.86)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   12  │    digits_ascii_upper    │ +p;ikqkhu}=jq!vs │           58 (5.86)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   13  │ digits_ascii_lower_punct │ ZGBNIWJXEUETHTRR │           26 (4.70)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   14  │ digits_ascii_upper_punct │ keimfxaaxrwoqmuq │           26 (4.70)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   15  │        hexdigits         │ [[&M?syglZ<pL${_ │           72 (6.17)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   16  │        hex_punct         │ sJrNGTmYqmYHSMQQ │           40 (5.32)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   17  │        hex_ascii         │ &_;_=_~[%?[{/[-, │           32 (5.00)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   18  │     hex_ascii_lower      │ J%OL+?HM+(?%.~SJ │           52 (5.70)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   19  │     hex_ascii_upper      │ }{$i<@s%gy+v#n}& │           52 (5.70)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   20  │  hex_ascii_lower_punct   │ NYMYVOIZLQITIWSP │           20 (4.32)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   21  │  hex_ascii_upper_punct   │ qqlmtmwsrnzskvxq │           20 (4.32)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   22  │        octdigits         │ ,zEOFCGI<<dH,}En │           85 (6.41)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   23  │        oct_punct         │ eNFEv8Oxv8oBLWkL │           54 (5.75)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   24  │        oct_ascii         │ +)'|}):*$%"&~;;9 │           34 (5.09)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   25  │     oct_ascii_lower      │ /+S)',D\[Z#SYCGM │           60 (5.91)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   26  │     oct_ascii_upper      │ zxp`m"dzz^<&r:to │           60 (5.91)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   27  │   oct_ascii_punct (UD)   │ [YlZ=A\x;O+I+>xY │           80 (6.32)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   28  │  oct_ascii_lower_punct   │ RXYGGTIANLESXMOW │           28 (4.81)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   29  │  oct_ascii_upper_punct   │ jllna9anxxt9ljzb │           28 (4.81)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   30  │         rfc_4122         │ W6KOMP9NXR3XMDMK │           36 (5.17)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
│   31  │       non_rfc_4122       │ ea4de14a9632eebb │           15 (3.91)           │
└───────┴──────────────────────────┴──────────────────┴───────────────────────────────┘
```
---
### Overview:

- The exclusion chart is a helpful tool for excluding specific characters from the generated key.
- The chart contains the index, key options, key samples, and the unique max key-size (entropy).
- The unique max key-size (entropy) is the maximum key size when the unique characters feature is enabled.
- The key samples are examples of the generated key using the specified key options.
- To exclude specific characters from the generated key, use the `exclude_chars` parameter with the index or key options.
---

### Obtain the Exclusion Chart:
***Please note that the exclusion chart can only be printed in `PrettyTable` format if the `prettytable` package is installed. Otherwise, the chart will be returned as a dictionary.***
- The exclusion chart can be printed and exported using the `print_echart` method.
- The chart can also be printed and exported using the `excluder_chart` function.
- The chart can be printed and exported in a tabular format using the `return_table` parameter.
- The chart can be exported to a file using the `fp` parameter.

#### Print and Export the Exclusion Chart:
```python
# Methods to print the exclusion chart to the console in a `PrettyTable` format.
# 'print' is not required when using these methods.
1. KeyCraftsman.print_echart()
2. excluder_chart()

# Export the exclusion chart to a file.
# Outputs a successful message when the chart is exported to the specified file path.
1. KeyCraftsman.print_echart(fp="excluder_chart.txt")
2. excluder_chart(fp="excluder_chart.txt")
```

#### Return the Exclusion Chart as a Dictionary:
```python
# Methods to return the exclusion chart as a dictionary.
# The dictionary contains the index, key options, key samples, and the unique max key-size (entropy).
# 'print' is required when using these methods.
1. KeyCraftsman.char_excluder(return_chart=True)
  1... KeyCraftsman.char_excluder(include_index=True) # Include the index in the dictionary.
2. excluder_chart(format_type="dict")
  2... excluder_chart(include_index=True, format_type="dict") # Include the index in the dictionary.
```

---
### How to Exclude Characters:

- *The `exclude_chars` parameter can be a string key type or integer index value from the exclusion chart.*
```python
`exclude_chars` = "punct" or 1  # Excludes punctuation characters from the generated key.
`exclude_chars` = "octo_ascii_upper_punct" or 29  # Excludes octal digits, uppercase ASCII letters, and punctuation characters.
`exclude_chars` = "ascii" or 2  # Excludes ASCII letters from the generated key.
`exclude_chars` = "ascii_lower" or 3  # Excludes lowercase ASCII letters from the generated key.
`exclude_chars` = "non_rfc_4122" or 31  # Excludes non-RFC 4122 compliant characters from the generated key. Useful for generating RFC 4122 compliant UUIDs character set.
```
---

### Whitespace Exclusion:

> ***Whitespace characters are automatically excluded from the charset.***
Additionally, if the exclude_chars parameter explicitly includes whitespace characters or is set to "whitespace," a warning message will be printed in verbose mode. 
---

## Seperator:

- The `sep` parameter is used to wrap the generated key with a custom separator.
  - If not specified, the key will **not** be wrapped with a separator.
  - When generating passkeys with a seperator, the seperator must be a single character of any standard characters (e.g., ascii_letters, digits).
  - When generating words with a seperator, the seperator must be 1 less than the word (`key_length`) length.
  - The separator must be a single character of any standard characters (e.g., ascii_letters, digits).
  - The `sep_width` parameter is used to specify the width for text wrapping when using separators.
    -  The width is only applicable when using separators.
    - The width must be 1 less than the key length to prevent the separator from being excluded.
    - If not specified, the default width is 4.

### Separator Examples:

- `sep=":"` will wrap the generated key with a colon separator.
- `sep_width=4` will wrap the generated key with a colon separator and a width of 4.
- `sep_width=(1, 5, 7)` will wrap the generated key with a colon separator at indexes 1, 5, and 7.

> ***If whitespace characters are detected in the specified separator, a warning message will be printed in verbose mode***
---


## Iterating Over the Class:

`KeyCraftsman` is an iterable class that can be iterated over the generated key(s) or word(s) depending on the `num_of_keys` parameter.
- If the `num_of_keys` parameter is not specified, the iterator will yield characters one at a time from the single generated key.
  - You can use a loop or other iteration constructs to process each character individually.
- If the `num_of_keys` parameter is specified, the class will iterate over the dictionary values of the generated keys.
  - This allows you to conveniently access and process each generated key when multiple keys are requested.

### Iteration Examples:

```python
kc = KeyCraftsman(key_length=32)
for k in kc:
    # Generate a single key without specifying the `num_of_keys` parameter.
    print(kc)
    # Output: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

kc = KeyCraftsman(key_length=32, num_of_keys=5)
for k in kc:
    # Generate multiple keys by specifying the `num_of_keys` parameter.
    print(kc)
    # Output:
    # 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    # 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    # 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    # 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    # 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```
---


## Unique Characters:
`KeyCraftsman` ensures that the generated key(s) or word(s) contain unique characters when the `unique_chars` parameter is enabled.

### Limitations:
- The unique character set is determined by the key options and the unique 
character limit.
- This feature is useful for users who need to generate unique keys for specific use cases.
- If the key length is larger than the length of the unique character set, an exception will be raised.
- If the generated key is already unique, a warning message will be printed in verbose mode.
- If the unique character limit is bypassed, a warning message will be printed in verbose mode.


### Bypass Unique Limit:
- The `bypass_unique_limit` parameter can be used to bypass the unique character limit.
- This feature is mainly for use cases where you need to generate unique passkeys for specific exclusion types that exceed the unique character limit for some.
---


## Encoded and URL-Safe Encoded Keys:
> ***The `encoded` and `urlsafe_encoded` parameters are mutually exclusive.***

The `encoded` and `urlsafe_encoded` parameters provide options for encoding the generated key(s) using base64 encoding.

When `encoded` is set to `True`, the generated key(s) will be encoded using standard base64 encoding. This encoding scheme is commonly used for various cryptographic and data serialization purposes.

On the other hand, setting `urlsafe_encoded` to `True` will utilize URL-safe base64 encoding. URL-safe encoding ensures that the generated key(s) can be safely included in URLs without causing any parsing issues. This is particularly useful when the generated keys need to be embedded in web applications or transmitted via URLs.

> ***Both encoding options offer flexibility in how the generated keys are represented and utilized. The choice between standard and URL-safe encoding depends on your specific use case and requirements.***


### Encoded and URL-Safe Encoded Examples:

```python
# Generate a standard encoded key.
key_gen = KeyCraftsman(key_length=32, encoded=True)
key = key_gen.key  # Retrieve a single encoded generated key.
print(key) # Output: b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Generate a URL-safe encoded key.
key_gen = KeyCraftsman(key_length=32, urlsafe_encoded=True)
key = key_gen.key  # Retrieve a single URL-safe encoded generated key.
print(key) # Output: b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Alternatively, the `encoded` and `urlsafe_encoded` parameters can be used to obtain multiple encoded keys.
key_gen = KeyCraftsman(key_length=32, num_of_keys=2, encoded=True) # Or urlsafe_encoded=True
keys = key_gen.keys  # Retrieve a dictionary of multiple encoded generated keys from the same instance.
print(keys) # Output: Keys(key1=b'...', key2=b'...')
```
---


## Obtain the Generated Key(s):

`KeyCraftsman` offers convenient methods to retrieve the generated key(s) or word(s) from the class instance. This functionality is designed to provide flexibility and ease of access for users requiring efficient retrieval of generated keys.

### Cached Properties:

- `key`: Cached property to retrieve a single generated key.
- `keys`: Cached property to retrieve a dictionary of multiple generated keys.
  - The `keys` property will default to 2 if the `num_of_keys` parameter is not specified.
  - The maximum number of keys is determined by the system's maximum integer size.
  - Returns a NamedTuple instance called `Keys` with each attribute named `key1`, `key2`, etc., up to the specified number of keys.
---

### Exporting the Generated Key(s):

> ***If `keyfile_name` is not specified, a default file name (generator_key(s).<bin/json>) will be used.***
- `export_key()`: Exports the generated key to a file.
- `export_keys()`: Exports multiple generated keys to a JSON file.
---


### Usage Examples:

```python
# Generate a single key and export it to a file.
key_gen = KeyCraftsman(key_length=32, keyfile_name="passkey-file")
key = key_gen.key  # Retrieve a single generated key.
keys = key_gen.keys  # Retrieve a namedtuple of multiple generated keys from the same instance.
key_gen.export_key()  # Export the generated key to a file.
key_gen.export_keys()  # Export multiple generated keys to a JSON file.
```
---


### Class Object Representation

The representation of `KeyCraftsman` is tailored to efficiently showcase the practical usage of the class object and its capabilities.

```python
def __repr__(self) -> str:
    """Returns a sample of generated keys"""
    return "\n".join(KeyCraftsman(key_length=12, sep="-", num_of_keys=10))

print(repr(KeyCraftsman()))

# Output:
bYh5-d2P6-HoHF
wIfp-jns0-1myP
0x5r-a3RU-7cMv
Lz8H-J5Lm-r4il
23m4-KQ6c-yPCJ
vdd0-BPo0-lQ7O
N62R-Go9T-XEYW
xjZj-zKmy-U4zC
fdQY-j0Eh-Ar91
2mdT-dMjl-Q3Qc
```

> ***This representation provides a glimpse of the generated keys, demonstrating the versatility and ease of use of the `KeyCraftsman` class.***
---


## Usage Examples:

```python
# Generate encoded or URLSafe-encoded keys.
key_gen = KeyCraftsman(key_length=32, num_of_keys=2, include_all_chars=False, encoded=True)

key = key_gen.key  # Retrieve a single encoded generated key.
keys = key_gen.keys  # Retrieve a dictionary of multiple encoded generated keys from the same instance.

key_gen.export_key()  # Export the generated key to a file.
key_gen.export_keys()  # Export multiple generated keys to a JSON file.

# Print the class object and export the exclusion chart for help in excluding characters.
print(key_gen)
print(key_gen.print_echart(return_table=True))  # PrettyTable object of the Exclusions Chart.
print(key_gen.print_echart(fp="exclusions_chart.txt"))  # Exclusions Chart exported to 'exclusions_chart.txt'.
# Alternatively, the exclusion chart can be printed and exported using the `excluder_chart` function.
e_chart = excluder_chart(return_table=True)  # PrettyTable object of the Exclusions Chart.
excluder_chart(fp="exclusions_chart.txt")  # Exclusions Chart exported to 'exclusions_chart.txt'.

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