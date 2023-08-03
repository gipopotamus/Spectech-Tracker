from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

from .forms import DocumentForm
from .models import Rental
from django.shortcuts import render


from django.shortcuts import render


@require_http_methods(["POST"])
def upload_documents(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    document_form = DocumentForm(request.POST, request.FILES)

    if document_form.is_valid():
        # Save each uploaded file separately
        for field_name, file in request.FILES.items():
            rental_field = getattr(rental, field_name)
            rental_field.save(file.name, file, save=True)

        # Redirect back to the rental detail page
        return redirect('rental_detail', pk=pk)

    # If the form is invalid, simply render the rental detail page with the form errors
    return render(request, 'rental_detail.html', {'rental': rental, 'document_form': document_form})