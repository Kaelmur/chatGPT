import io
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Work
from .forms import TextForm
from django.contrib import messages
from docx import Document
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from chatgpt.settings import MEDIA_ROOT


def home(request):
    return render(request, 'app/index.html', {
    })


@login_required
def text(request):
    if request.method == "POST":
        t_form = TextForm(request.POST, request.FILES, instance=request.user)
        if t_form.is_valid():
            doc = Document(request.FILES.get("file"))
            fulltext = []
            for para in doc.paragraphs:
                fulltext.append(para.text)
            fulltext = '\n'.join(fulltext)
            n_text = Work(file=fulltext, user=request.user)
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
    doc.add_paragraph(str(file.file))
    target_stream = io.BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    response = FileResponse(target_stream,
                            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{file.id}.docx"'
    return response
