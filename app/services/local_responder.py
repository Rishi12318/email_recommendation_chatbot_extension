from datetime import datetime

CATEGORY_LABELS = {
    "deadline": "deadline/assessment",
    "interview_call": "interview invitation",
    "news": "newsletter/promotion",
    "confirmation_email": "order confirmation",
    "otp": "verification code",
    "expired_email": "expired email",
    "other": "general",
}

CATEGORY_ACTIONS = {
    "deadline": "Set a reminder",
    "interview_call": "Keep and prepare",
    "news": "Archive",
    "confirmation_email": "Archive after review",
    "otp": "Delete after use",
    "expired_email": "Delete",
    "other": "Keep",
}

def generate_response(query, search_results, classifications=None):
    if not search_results:
        return "No emails found matching your query."

    count = len(search_results)
    senders = set()
    subjects = []
    categories = []

    for r in search_results:
        email_text = r.get("email", "")
        lines = email_text.split("\n")
        for line in lines:
            if line.startswith("From:"):
                senders.add(line.replace("From:", "").strip())
            elif line.startswith("Subject:"):
                subjects.append(line.replace("Subject:", "").strip())

    classification_info = ""
    if classifications:
        cat_counts = {}
        for c in classifications:
            cat = c.get("category", "other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if cat_counts:
            cats = [f"{count} {CATEGORY_LABELS.get(c, c)}" for c, count in sorted(cat_counts.items(), key=lambda x: -x[1])]
            classification_info = " Categories: " + ", ".join(cats) + "."

    sender_info = ""
    if senders:
        sender_list = ", ".join(list(senders)[:3])
        if len(senders) > 3:
            sender_list += f" and {len(senders)-3} more"
        sender_info = f" from {sender_list}"

    response = f"Found {count} email{'' if count == 1 else 's'}{sender_info}.{classification_info}"

    if subjects:
        response += f"\n\nHighlights:\n" + "\n".join(f"- {s[:80]}" for s in subjects[:3])

    if classifications:
        top_cat = classifications[0].get("category", "other")
        action = CATEGORY_ACTIONS.get(top_cat, "Review")
        response += f"\n\nRecommendation: {action}"

    return response

def generate_summary(emails, classifications=None):
    if not emails:
        return "No emails to summarize."
    total = len(emails)
    cat_counts = {}
    if classifications:
        for c in classifications:
            cat = c.get("category", "other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
    response = f"You have {total} email{'' if total == 1 else 's'}."
    if cat_counts:
        parts = [f"{count} {CATEGORY_LABELS.get(c, c)}" for c, count in sorted(cat_counts.items(), key=lambda x: -x[1])]
        response += " " + ", ".join(parts) + "."
    return response

def generate_action_recommendation(email_text, category):
    action = CATEGORY_ACTIONS.get(category, "Review")
    label = CATEGORY_LABELS.get(category, "email")
    return f"[{action}] {label}: {email_text[:100]}..."
