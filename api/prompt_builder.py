from typing import Any

SYSTEM_PROMPT = (
    "You are an ecommerce analytics assistant for a single merchant. "
    "Only use the summarized performance data provided by the system. "
    "Do not invent data, do not access any external systems, and do not repeat raw database rows. "
    "Provide actionable insights, risk alerts, recommendations, and next actions for ecommerce profitability, inventory, and marketplace growth."
)

USER_PROMPT_TEMPLATE = (
    "User query: {user_message}\n"
    "Marketplace platform: {platform_code}\n"
    "Intent: {intent}\n"
    "Analytics summary:\n{analytics_summary}\n"
    "Answer as an ecommerce analyst, marketplace consultant, profit optimization advisor, inventory advisor, and sales growth assistant. "
    "Focus on the merchant's own data and avoid generic assistant behavior."
)


class PromptBuilder:
    @staticmethod
    def build_messages(user_message: str, intent: str, analytics_summary: dict[str, Any], platform_code: str | None = None) -> list[dict[str, str]]:
        summary_lines = []
        for key, value in analytics_summary.items():
            if isinstance(value, list):
                if value:
                    summary_lines.append(f"{key}:")
                    for item in value[:5]:
                        summary_lines.append(f"  - {item}")
                continue
            summary_lines.append(f"{key}: {value}")

        analytics_text = "\n".join(summary_lines)

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    user_message=user_message,
                    platform_code=platform_code or "all platforms",
                    intent=intent,
                    analytics_summary=analytics_text,
                ),
            },
        ]
