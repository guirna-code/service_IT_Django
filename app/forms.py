from django import forms

from .models import Composant, Machine, RapportIntervention, Utilisateur


class BootstrapFormMixin:
    select_widgets = (forms.Select, forms.SelectMultiple)
    text_widgets = (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.DateInput, forms.Textarea)

    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, self.select_widgets) else "form-control"
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} {css_class}".strip()


class MachineForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Machine
        fields = ["nom", "numero_serie", "type", "pole", "date_acquisition", "etat"]
        widgets = {
            "date_acquisition": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_nom(self):
        return self.cleaned_data.get("nom", "").strip()

    def clean_numero_serie(self):
        numero_serie = self.cleaned_data.get("numero_serie")
        if not numero_serie:
            return None

        numero_serie = numero_serie.strip()
        duplicate = Machine.objects.filter(numero_serie=numero_serie)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)

        if duplicate.exists():
            raise forms.ValidationError("Ce numero de serie est deja utilise.")

        return numero_serie


class MachineStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Machine
        fields = ["etat"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class ComposantForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Composant
        fields = ["nom", "type", "etat", "machine", "marque", "numero_serie", "date_installation"]
        widgets = {
            "date_installation": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["machine"].queryset = Machine.objects.order_by("nom")
        self.apply_bootstrap_classes()

    def clean_nom(self):
        return self.cleaned_data.get("nom", "").strip()


class RapportInterventionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RapportIntervention
        fields = [
            "machine_concernee",
            "technicien",
            "type",
            "statut",
            "date",
            "duree",
            "description",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["machine_concernee"].queryset = Machine.objects.order_by("nom")
        self.fields["technicien"].queryset = Utilisateur.objects.filter(
            role="technician",
            is_active=True,
        ).order_by("email")

        required_fields = ["machine_concernee", "type", "statut", "date", "duree", "description"]
        for field_name in required_fields:
            self.fields[field_name].required = True

        if user and getattr(user, "role", None) == "technician":
            self.fields["technicien"].required = False
        else:
            self.fields["technicien"].required = True

        self.apply_bootstrap_classes()

    def clean_duree(self):
        duree = self.cleaned_data.get("duree")
        if duree is None:
            raise forms.ValidationError("La duree est obligatoire.")
        if duree < 0:
            raise forms.ValidationError("La duree ne peut pas etre negative.")
        return duree

    def clean_description(self):
        return self.cleaned_data.get("description", "").strip()

    def clean(self):
        cleaned_data = super().clean()
        if self.user and getattr(self.user, "role", None) == "technician":
            cleaned_data["technicien"] = self.user
        return cleaned_data


class UtilisateurForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["email", "first_name", "last_name", "role", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        duplicate = Utilisateur.objects.filter(email=email)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)

        if duplicate.exists():
            raise forms.ValidationError("Cet email est deja utilise.")

        return email
