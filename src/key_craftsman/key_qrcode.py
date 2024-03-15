import operator
import pyperclip
from functools import partial
from pathlib import Path
from qrcode.main import QRCode
from qrcode.constants import *
from qrcode.exceptions import DataOverflowError
from typing import AnyStr, Literal, Union

from .key_craftsman import KeyCraftsman


class KeyQRCode:
    """
    Generate a QR code from a given key and save it as an image file with the key copied to clipboard.
    
    ### Args:
        - `key` : AnyStr : The text to be encoded in the QR code.
        - `version` : int : The version of the QR code to be generated. Default is 4.
        - `file_name` : Union[Path, str] : The name of the file to save the QR code image. Default is an empty string.
            - If not provided, a unique file name is generated.
    
    ### Methods:
        - `generate_qr(clipboard_only: bool=False)` : Generate the QR code and save it as an image file with the key copied to clipboard.
            - `clipboard_only` : bool : If True, the QR code is not displayed and only the key is copied to clipboard. Default is False.
            - If the `file_name` is provided, the QR code image is saved with the specified name.
    
    ### Example:
    ```python
    key = KeyCraftsman(key_length=18, sep="-", sep_width=range(6, 12, 18), unique_chars=True).key
    KeyQRCode(key=key, version=4).generate_qr(clipboard_only=True)
    # Output: Text copied to clipboard.
    
    key = KeyCraftsman(key_length=18, sep="-", sep_width=range(6, 12, 18), unique_chars=True).key
    KeyQRCode(key=key, version=4, file_name="QRCode").generate_qr()
    # Output: The generated QR code which also gets saved.
    ```
    """
    
    def __init__(
        self, key: Union[AnyStr, int, float], version: int = 4, file_name: Union[Path, str] = "",
    ) -> None:
        self._key = key
        self._version = self._validate_version(version)
        self._fp = self._check_filename(file_name)
        self._keysize = self._get_ksize()
        self._clevel = self._correction_level(self._keysize)
        self._save = False

    def _check_filename(self, file_name) -> Union[str, Path]:
        if file_name and isinstance(file_name, (Path, str)):
            fp =  Path(file_name).stem
        else:
            fp = Path("QRCODE_" + self._unique_id())
        
        def isfile(f):
            if f.is_file():
                f = f.as_posix().stem + f"_{self._unique_id()}"
            return f
        return isfile(fp)
    
    def _validate_version(self, version: int) -> Union[QRCode, Literal[4]]:
        try:
            _ = QRCode(version=version)
            return version
        except ValueError:
            return 4

    def _get_ksize(self) -> int:
        if hasattr(self._key, "__len__"):
            return len(self._key)

    def _unique_id(self) -> str:
        return KeyCraftsman(
            key_length=4, unique_chars=True, exclude_chars="ascii_upper_punct"
        ).key

    def _correction_level(self, size: int) -> int:
        lessthan = partial(operator.lt, size)

        if any((not size, not hasattr(size, "__lt__"), lessthan(50))):
            return ERROR_CORRECT_L
        elif lessthan(200):
            level = ERROR_CORRECT_M
        elif lessthan(1000):
            level = ERROR_CORRECT_Q
        else:
            level = ERROR_CORRECT_H
        return level
    
    def generate_qr(self, show_qr: bool=True, clipboard: bool=True, save_qr: bool=False) -> None:
        """
        Generate the QR code and save it as an image file with the key copied to clipboard.
        
        ### Args:
            - `show_qr`: bool : If True, the QR code is displayed. Default is False.
            - `clipboard`: bool : If True, the key is copied to clipboard. Default is True.
            - `save_qr`: bool : If True, the QR code image is saved. Default is False.
        
        ### Raises:
            - `DataOverflowError`: If the data provided is too large to fit in the selected QR code version and error correction level.
            - `IOError`: If an error occurs while trying to save the QR code image file.
            - `ValueError`: If an error occurs while trying to copy the specified text to clipboard.
        """
        
        try:
            # Generate QR code with the text
            qr = QRCode(version=self._version, error_correction=self._clevel)
            qr.add_data(self._key, optimize=0)
            qr.make(fit=True)

            # Create an image from the QR code
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Display the QR code
            if show_qr:
                qr_image.show()

            # Save the QR code image
            try:
                if save_qr:
                    qr_image.save(self._fp.with_suffix(".png"))
                    print(f"QR code saved as {self._fp}.png")
            except IOError as save_error:
                raise save_error(
                    f"Failed trying to save QR code image file {self._fp}."
                )

            # Copy the text to clipboard
            try:
                if clipboard:
                    pyperclip.copy(self._key)
                    print("Text copied to clipboard.")
            except pyperclip.PyperclipException as clipboard_error:
                raise ValueError(
                    "An error occured while trying to copy specified text to clipboard."
                    f"\n{clipboard_error}"
                )

        except DataOverflowError:
            raise DataOverflowError("Data provided is too large to fit in the selected QR code version and error correction level.")