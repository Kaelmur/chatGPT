import base64
import io
import os

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Work
from .forms import TextForm
from docx import Document
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import mammoth as mth
from htmldocx import HtmlToDocx
import requests


def home(request):
    return render(request, 'app/index.html', {
    })


def ignore_image(image):
    return []

@login_required
def text(request):
    if request.method == "POST":
        t_form = TextForm(request.POST, request.FILES, instance=request.user)
        if t_form.is_valid():
            doc = mth.convert_to_html(request.FILES.get("file"), convert_image=ignore_image)
            n_text = Work(file=doc.value, user=request.user)
            n_text.save()
        return redirect(request.path_info)
    else:
        form = TextForm()
        try:
            latest = Work.objects.latest("id")
        except:
            latest = None

    return render(request, "app/index.html", {
        "form": form,
        "text": latest
    })


def download_file(request, file_id):
    file = get_object_or_404(Work, pk=file_id)
    doc = Document()
    file_content = str(file.file)
    file.file.close()
    key = os.environ.get("yandex_key")
    response = requests.get(url=f"https://translate.yandex.net/api/v1.5/tr.json/translate", params={"key": key,
                                                                                                    "text": file_content,
                                                                                                    "lang": "ru",
                                                                                                    "format": "html"})
    response.raise_for_status()
    data = response.json()
    translated_text = str(data["text"][0])
    prompt = {
        "modelUri": f"gpt://{os.environ.get('folder_api')}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты бот, который поможет с html текстом не оставляя сообщения о проделанной работе"
            },
            {
                "role": "user",
                "text": f"Перефразируй и оставь html аттрибуты в тексте: {translated_text}"
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {os.environ.get('yandexgpt_api')}"
    }
    result = requests.post(url, headers=headers, json=prompt)
    r = result.json()
    new_parser = HtmlToDocx()
    new_parser.add_html_to_document(r['result']['alternatives'][0]['message']['text'], doc)
    target_stream = io.BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    response = FileResponse(target_stream,
                            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{file.id}.docx"'
    return response
