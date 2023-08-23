from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Rental
from .forms import DocumentForm


def upload_documents(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    if request.method == 'POST':
        document_form = DocumentForm(request.POST, request.FILES)
        if document_form.is_valid():
            # Сохраняем каждый загружаемый файл отдельно
            for field_name, file in request.FILES.items():
                # Получаем соответствующее поле модели Rental по его имени
                field = getattr(rental, field_name)
                # Сохраняем файл в соответствующее поле модели Rental
                field.save(file.name, file, save=True)

            # После успешной загрузки документов, перенаправляем на страницу с деталями аренды
            return redirect('rental_detail', pk=pk)  # Замените 'rental_detail' на ваш URL pattern

        else:
            # Если форма невалидна, вернем ошибку с соответствующим статусом
            # и передадим параметры ошибки в URL для дальнейшего отображения на странице
            error_params = "?error=invalid_form"
            return redirect('rental_detail', pk=pk) + error_params  # Замените 'rental_detail' на ваш URL pattern

    # Если метод запроса не POST, вернем ошибку с соответствующим статусом
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
