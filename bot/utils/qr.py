import qrcode
import io
import os
from PIL import Image

def generate_upi_qr(upi_id, name="Surface Hub", amount=100):
    """
    Generates a UPI payment QR code as a BytesIO object.
    Format: upi://pay?pa=ID&pn=NAME&am=AMOUNT&cu=INR
    """
    upi_url = f"upi://pay?pa={upi_id}&pn={name.replace(' ', '%20')}&am={amount}&cu=INR"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr
