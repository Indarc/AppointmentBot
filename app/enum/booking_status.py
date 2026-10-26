from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending" # The booking has been created but not yet confirmed by the specialist.
    CONFIRMED = "confirmed" # The booking has been confirmed by the specialist and is scheduled to take place.
    CANCELLED = "cancelled" # The booking has been cancelled by either the user or the specialist.
    COMPLETED = "completed" # The booking has been completed successfully.
    NO_SHOW = "no_show" # The user did not show up for the booking, and the specialist marked it as a no-show.

class BookingDeleteReason(str, Enum):
    USER_CANCELLED = "user_cancelled" # The user cancelled the booking.
    SPECIALIST_CANCELLED = "specialist_cancelled" # The specialist cancelled the booking.
    OTHER = "other" # Any other reason for cancellation not covered by the above categories.