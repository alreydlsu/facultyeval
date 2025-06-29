# 📋 Classroom Evaluation Form (with Email PDF Export)

This Streamlit app provides a digital version of a classroom evaluation form. After submission, a PDF copy of the completed form is automatically emailed to the user.

## ✅ Features

- Faculty and evaluator info capture
- Four structured evaluation domains
- Optional signature input
- Auto-calculated area and overall means
- **PDF generation and automatic email sending**
- Streamlit-based UI, ready for local or cloud deployment

## 📩 Email Setup

To enable PDF emailing, configure the SMTP section inside `app.py`:
```python
server.login("your_email@gmail.com", "your_app_password")
```

Use an [App Password](https://support.google.com/accounts/answer/185833) for secure authentication.

## 🖥️ How to Run

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

## 🔒 Environment Notes

- Ensure internet access is available for SMTP
- Email address is **not stored or included in the PDF**
- The form does **not log data externally**

## 📸 Preview

![Preview](assets/thumbnail.png)

---

© 2025 | Streamlit Email Evaluation Form by Dr. Al Rey Villagracia