from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from .forms import UserRegisterForm, UserUpdateForm
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model


@user_passes_test(lambda u: not u.is_authenticated, login_url='c-home')
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Your account {username} has been created! Now you can Login.")
            return redirect("login")
    else:
        form = UserRegisterForm()
    return render(request, "users/register.html", {
        'form': form,
    })


@login_required
def profile(request):
    if request.method == "POST":
        reset_email(request)
        return redirect('profile')
    return render(request, 'users/profile.html', {
    })


def reset(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been updated")
            return redirect('profile')
        else:
            form = UserUpdateForm(instance=request.user)
        return render(request, 'users/profile.html', {
            'form': form,
            'reset': True
        })
    else:
        messages.error(request, "Activation link is invalid.")
    return redirect('profile')


@login_required
def reset_email(request):
    email = request.user.email
    user = request.user
    token = default_token_generator.make_token(user)
    mail_subject = "Verify your email change."
    message = render_to_string('users/template_change_email.html', {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token,
        'protocol': "https" if request.is_secure() else "http",
    })
    email_send = EmailMessage(mail_subject, message, to=[email])
    if email_send.send():
        messages.success(request, f"Dear {user}, please got to your email {email} inbox and click on "
                                  f"received activation link to confirm email change. Note: Check your spam"
                                  f" folder.")
    else:
        messages.error(request, f"Problem sending email to {email}, please check if you typed it correctly.")
