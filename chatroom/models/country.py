from django.db import models
from django.utils.text import slugify
from django.core.validators import MinLengthValidator


class Country(models.Model):
    """
    Model representing a country.
    """
    name = models.CharField(
        max_length=220,
        unique=True,
        verbose_name="Country Name",
        help_text="Enter the official country name.",
        validators=[MinLengthValidator(2)]
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name="Country Slug",
        help_text="Auto-generated slug from the country name."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Status",
        help_text="Mark as active if the country is currently available."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created Date",
        help_text="The date and time when the country was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated Date",
        help_text="The date and time when the country was last updated."
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def total_chatrooms(self):
        """Returns the total number of chat rooms in the country."""
        return self.chatroom.count() if hasattr(self, 'chatroom') else 0

    def activate(self):
        """Activate the country."""
        self.is_active = True
        self.save()

    def deactivate(self):
        """Deactivate the country."""
        self.is_active = False
        self.save()


class State(models.Model):
    """
    Model representing a state within a country.
    """
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="states",
        verbose_name="Country",
        help_text="Select the country this state belongs to."
    )
    name = models.CharField(
        max_length=255,
        verbose_name="State Name",
        help_text="Enter the state name.",
        validators=[MinLengthValidator(2)]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created Date",
        help_text="The date and time when the state was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated Date",
        help_text="The date and time when the state was last updated."
    )

    class Meta:
        unique_together = ("country", "name")
        ordering = ("name",)
        verbose_name = "State"
        verbose_name_plural = "States"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country", "name"]),
        ]

    def __str__(self):
        return f"{self.name}, {self.country.name}"

    def get_country_name(self):
        """Returns the country name."""
        return self.country.name
