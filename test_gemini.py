from app.services.ai_service import summarize_document

result = summarize_document(
    """
    Employees are entitled to 21 days annual leave.
    Sick leave is granted upon medical approval.
    """
)

print(result)