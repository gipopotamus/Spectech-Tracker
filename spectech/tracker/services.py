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

            # Формируем словарь с информацией о загруженных документах
            documents = {}
            for field_name in document_form.fields.keys():
                file_field = getattr(rental, field_name)
                if file_field and file_field.url:
                    documents[field_name] = {
                        'file_url': file_field.url,
                        'file_name': file_field.name.split('/')[-1],  # Получаем имя файла из URL
                    }

            # Возвращаем список документов в виде JSON-ответа
            return JsonResponse(documents, safe=False)
        else:
            # Если форма невалидна, вернем ошибку с соответствующим статусом
            return JsonResponse({'error': 'Форма невалидна'}, status=400)

    # Если метод запроса не POST, вернем ошибку с соответствующим статусом
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)