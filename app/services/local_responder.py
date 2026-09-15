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


REPLY_TEMPLATES = {
    "greeting": "Hi, thank you for your email. I'll get back to you shortly.",
    "meeting": "Thanks for reaching out. I'm available for a meeting. Please share a few time slots that work for you, and I'll confirm.",
    "deadline": "Received, I'll make sure to complete this before the deadline.",
    "interview": "Thank you for the interview invitation. I'm excited about this opportunity and will confirm my availability shortly.",
    "question": "Thanks for your question. I'll look into this and get back to you with a detailed response.",
    "approval": "Approved. Please proceed with the next steps.",
    "follow_up": "Thanks for following up. I'm working on this and will share an update soon.",
    "default": "Thank you for your email. I've reviewed your message and will respond in detail shortly.",
}


def generate_reply(email_text: str, similar_emails: list = None) -> str:
    """Generate a reply recommendation based on the email content."""
    lower = email_text.lower()

    if any(w in lower for w in ["interview", "scheduled", "position", "hiring"]):
        template = REPLY_TEMPLATES["interview"]
    elif any(w in lower for w in ["meeting", "schedule", "calendar", "available"]):
        template = REPLY_TEMPLATES["meeting"]
    elif any(w in lower for w in ["deadline", "due", "submit", "complete by"]):
        template = REPLY_TEMPLATES["deadline"]
    elif any(w in lower for w in ["approve", "approval", "confirmed", "agreed"]):
        template = REPLY_TEMPLATES["approval"]
    elif any(w in lower for w in ["question", "how", "what", "when", "where", "could you"]):
        template = REPLY_TEMPLATES["question"]
    elif any(w in lower for w in ["follow up", "following up", "any update", "checking in"]):
        template = REPLY_TEMPLATES["follow_up"]
    elif any(w in lower for w in ["hello", "hi", "dear", "hey"]):
        template = REPLY_TEMPLATES["greeting"]
    else:
        template = REPLY_TEMPLATES["default"]

    if similar_emails:
        context_snippet = similar_emails[0].get("email", "")[:150]
        template += f"\n\n(Reference: similar past email — \"{context_snippet}...\")"

    return template
