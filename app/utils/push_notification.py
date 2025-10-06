"""
Push notification utilities using Expo Push Notifications
"""

from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage


def send_push_notification(
    tokens: list[str], title: str, body: str, data: dict | None = None
):
    """
    Send push notifications to multiple Expo push tokens

    Args:
        tokens: List of Expo push tokens
        title: Notification title
        body: Notification body
        data: Optional additional data to send with notification
    """
    if not tokens:
        return

    # Filter out invalid tokens
    valid_tokens = [token for token in tokens if PushClient.is_exponent_push_token(token)]

    if not valid_tokens:
        return

    # Create messages
    messages = [
        PushMessage(
            to=token,
            title=title,
            body=body,
            data=data or {},
            sound="default",
            priority="high",
        )
        for token in valid_tokens
    ]

    try:
        PushClient().publish_multiple(messages)
    except DeviceNotRegisteredError:
        pass
    except Exception:
        pass
