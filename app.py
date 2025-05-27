from flask import Flask, render_template, request, jsonify, send_file
import firebase_admin
from firebase_admin import credentials, db
from fpdf import FPDF
import datetime
import os
import pytz
import qrcode
import io

app = Flask(__name__)

# Firebase Initialization
cred = credentials.Certificate("D:/smart car updated/Smart_Car_Parking/Smart_Car_Parking/smart-car-parking-f5696-firebase-adminsdk-fbsvc-cf2477d3fa.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://smart-car-parking-f5696-default-rtdb.firebaseio.com"})

# रिपोर्ट फाइल सेव करने की डायरेक्टरी
REPORTS_DIR = "D:/PYTHON_PROJECT/Smart_Car_Parking/reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

FONT_PATH = "D:/PYTHON_PROJECT/fonts/DejaVuSans.ttf"  # DejaVuSans.ttf का सही पथ दें

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

def generate_qr_code(data, size=100):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/status")
def get_status():
    ref = db.reference("/Parking")
    parking_data = ref.get()
    return jsonify(parking_data)

@app.route("/save_start_time", methods=["POST"])
def save_start_time():
    try:
        data = request.json
        slot = data["slot"]
        start_time = datetime.datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
        start_time = start_time.astimezone(IST)
        
        ref = db.reference(f"/Reports/{slot}")
        report_data = ref.get() or {}
        
        # Save start time only if it's not already saved
        if "start_timestamp" not in report_data:
            report_data.update({
                "start_time": start_time.strftime("%I:%M %p"),
                "start_timestamp": start_time.timestamp(),
                "date": start_time.strftime("%Y-%m-%d"),
                "day": start_time.strftime("%A")
            })
            ref.set(report_data)
            return jsonify({"message": "Start time saved successfully!"})
        return jsonify({"message": "Start time already exists"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_report", methods=["POST"])
def save_report():
    try:
        data = request.json
        slot = data["slot"]
        
        ref = db.reference(f"/Reports/{slot}")
        report_data = ref.get() or {}
        
        # Get exit time
        exit_time = datetime.datetime.fromisoformat(data["exit_time"].replace('Z', '+00:00'))
        exit_time = exit_time.astimezone(IST)
        
        # Get start time from request
        start_time = datetime.datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
        start_time = start_time.astimezone(IST)
        
        report_data.update({
            "name": data["name"],
            "contact": data["contact"],
            "vehicle": data["vehicle"],
            "email": data["email"],
            "slot": slot,
            "start_time": start_time.strftime("%I:%M %p"),
            "start_timestamp": start_time.timestamp(),
            "exit_time": exit_time.strftime("%I:%M %p"),
            "exit_timestamp": exit_time.timestamp(),
            "date": start_time.strftime("%Y-%m-%d"),
            "day": start_time.strftime("%A")
        })
        ref.set(report_data)
        return jsonify({"message": "Report saved successfully!"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_report")
def download_report():
    slot = request.args.get("slot")
    
    if not slot:
        return "⚠️ Slot number is required", 400
        
    ref = db.reference(f"/Reports/{slot}")
    report_data = ref.get()
    
    if not report_data:
        return "⚠️ Report not found", 404

    try:
        # Get current time for exit if not already set
        current_time = datetime.datetime.now(IST)
        
        # Ensure start time exists
        if "start_timestamp" not in report_data:
            report_data["start_time"] = current_time.strftime("%I:%M %p")
            report_data["start_timestamp"] = current_time.timestamp()
            report_data["date"] = current_time.strftime("%Y-%m-%d")
            report_data["day"] = current_time.strftime("%A")
            ref.set(report_data)
        
        # If exit time not set, use current time
        if "exit_timestamp" not in report_data:
            report_data["exit_time"] = current_time.strftime("%I:%M %p")
            report_data["exit_timestamp"] = current_time.timestamp()
            ref.set(report_data)
        
        # Get times from stored timestamps
        start_time = datetime.datetime.fromtimestamp(report_data["start_timestamp"])
        start_time = IST.localize(start_time)
        
        exit_time = datetime.datetime.fromtimestamp(report_data["exit_timestamp"])
        exit_time = IST.localize(exit_time)
        
        # Calculate parking duration in minutes
        parking_duration = (exit_time - start_time).total_seconds() / 60
        
        # Calculate charges
        base_price = 50
        hours_parked = parking_duration / 60
        extra_hours = max(0, hours_parked - 0.5)  # First 30 minutes are free
        extra_charge = round(extra_hours) * 10  # Rs. 10 per hour after first 30 minutes
        total_charge = base_price + extra_charge

        filename = os.path.join(REPORTS_DIR, f"{slot}_parking_report.pdf")

        pdf = FPDF()
        pdf.add_page()
        
        # Set up fonts
        pdf.set_font("Arial", "B", 16)

        # Add header with logo and title
        pdf.cell(0, 20, "Smart Car Parking", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "Parking Invoice", ln=True, align="C")
        pdf.ln(10)

        # Add a line separator
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

        # Customer Information Section
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Customer Information", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(40, 10, "Name:", ln=False)
        pdf.cell(0, 10, report_data['name'], ln=True)
        pdf.cell(40, 10, "Contact:", ln=False)
        pdf.cell(0, 10, report_data['contact'], ln=True)
        pdf.cell(40, 10, "Vehicle No:", ln=False)
        pdf.cell(0, 10, report_data['vehicle'], ln=True)
        pdf.cell(40, 10, "Email:", ln=False)
        pdf.cell(0, 10, report_data['email'], ln=True)
        pdf.ln(10)

        # Parking Details Section
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Parking Details", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(40, 10, "Slot No:", ln=False)
        pdf.cell(0, 10, slot, ln=True)
        pdf.cell(40, 10, "Date:", ln=False)
        pdf.cell(0, 10, report_data['date'], ln=True)
        pdf.cell(40, 10, "Day:", ln=False)
        pdf.cell(0, 10, report_data['day'], ln=True)
        pdf.cell(40, 10, "Entry Time:", ln=False)
        pdf.cell(0, 10, report_data['start_time'], ln=True)
        pdf.cell(40, 10, "Exit Time:", ln=False)
        pdf.cell(0, 10, report_data['exit_time'], ln=True)
        
        # Format parking duration
        hours = int(parking_duration // 60)
        minutes = int(parking_duration % 60)
        duration_str = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
        pdf.cell(40, 10, "Duration:", ln=False)
        pdf.cell(0, 10, duration_str, ln=True)
        pdf.ln(10)

        # Charges Section with table-like format
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Charges Breakdown", ln=True)
        pdf.set_font("Arial", "", 12)
        
        # Table header
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(120, 10, "Description", 1, 0, "L", True)
        pdf.cell(70, 10, "Amount (Rs.)", 1, 1, "R", True)
        
        # Table rows
        pdf.cell(120, 10, "Base Price", 1, 0, "L")
        pdf.cell(70, 10, str(base_price), 1, 1, "R")
        
        if extra_charge > 0:
            pdf.cell(120, 10, f"Extra Charges ({round(extra_hours)} hours @ Rs. 10/hour)", 1, 0, "L")
            pdf.cell(70, 10, str(extra_charge), 1, 1, "R")
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(120, 10, "Total Amount", 1, 0, "L", True)
        pdf.cell(70, 10, str(total_charge), 1, 1, "R", True)
        pdf.ln(20)

        # Payment QR Codes Section
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Payment Options", ln=True, align="C")
        pdf.ln(10)

        # Generate and add dummy UPI QR code
        upi_qr_data = "upi://dummy/payment"
        upi_qr_image = generate_qr_code(upi_qr_data)
        upi_qr_filename = os.path.join(REPORTS_DIR, f"{slot}_upi_qr.png")
        with open(upi_qr_filename, "wb") as f:
            f.write(upi_qr_image)
        pdf.image(upi_qr_filename, x=50, y=pdf.get_y(), w=50)
        pdf.cell(50, 10, "UPI Payment", ln=False, align="C")
        pdf.ln(60)

        # Generate and add dummy Paytm QR code
        paytm_qr_data = "https://dummy.paytm.com"
        paytm_qr_image = generate_qr_code(paytm_qr_data)
        paytm_qr_filename = os.path.join(REPORTS_DIR, f"{slot}_paytm_qr.png")
        with open(paytm_qr_filename, "wb") as f:
            f.write(paytm_qr_image)
        pdf.image(paytm_qr_filename, x=100, y=pdf.get_y() - 50, w=50)
        pdf.cell(50, 10, "Paytm Payment", ln=True, align="C")
        pdf.ln(20)

        # Footer
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "Thank you for choosing Smart Car Parking!", ln=True, align="C")
        pdf.cell(0, 10, "For any queries, contact: support@smartcarparking.com", ln=True, align="C")
        pdf.cell(0, 10, "This is a computer-generated invoice. No signature required.", ln=True, align="C")

        pdf.output(filename)

        # Clean up QR code files
        os.remove(upi_qr_filename)
        os.remove(paytm_qr_filename)

        return send_file(filename, as_attachment=True)
    
    except Exception as e:
        return f"Error generating report: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
