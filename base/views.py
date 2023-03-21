from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import RoomForm
from .models import Message, Room, Topic


@login_required(login_url="login")
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    room_id = message.room.id
    print(message.user, room_id, request.user)
    if request.user != message.user:
        return HttpResponse("You are not to allowed delete")

    if request.method == "POST":
        message.delete()
        return redirect("room", pk=room_id)
    return render(request, "base/delete.html", {"obj": message})


def loginPage(request):
    page = "login"
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username").lower()
        password = request.POST.get("password")
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "user does not exist!!")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "username or password does not exist!!")
    context = {"page": page}
    return render(request, "base/login_register.html", context)


def regitsterPage(request):
    form = UserCreationForm()
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Error Occured During Registration!!")
    return render(
        request, "base/login_register.html", {"page": "register", "form": form}
    )


def logutUser(request):
    page = "logout"
    logout(request)
    return redirect("home")


def home(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q)
    )

    activity = Message.objects.filter(Q(room__topic__name__icontains=q))
    rooms_count = rooms.count()
    topics = Topic.objects.all()
    context = {
        "rooms": rooms,
        "topics": topics,
        "rooms_count": rooms_count,
        "activites": activity,
    }
    return render(request, "base/home.html", context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by(
        "-created"
    )  # many to one relationships here
    participants = room.participants.all()  # many to  many relationship here

    if request.method == "POST":
        messge = Message.objects.create(
            user=request.user, room=room, body=request.POST.get("body")
        )
        # if participants.count(request.user) == 0:
        room.participants.add(request.user)
        return redirect("room", pk=room.id)

    context = {
        "room": room,
        "room_messages": room_messages,
        "participants": participants,
    }
    return render(request, "base/room.html", context)


@login_required(login_url="login")
def createRoom(request):
    form = RoomForm()
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    context = {"form": form}
    return render(request, "base/room_form.html", context)


@login_required(login_url="login")
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)  # form will be prefilled with room value

    if request.user != room.host:
        return HttpResponse("Your are not allowed here!!")

    if request.method == "POST":
        form = RoomForm(
            request.POST, instance=room
        )  # identify which room value will update/replace
        if form.is_valid():
            form.save()
            return redirect("home")
    context = {"form": form}
    return render(request, "base/room_form.html", context)


@login_required(login_url="login")
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse("Your are not allowed here!!")

    if request.method == "POST":
        room.delete()
        return redirect("home")
    return render(request, "base/delete.html", {"obj": room})
