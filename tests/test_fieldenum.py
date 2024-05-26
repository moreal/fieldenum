# type: ignore

import pickle
from typing import Any, Self

import pytest
from fieldenum import Unit, Variant, fieldenum, unreachable
from fieldenum.exceptions import NotAllowedError


@fieldenum
class Message:
    Quit = Unit
    Move = Variant(x=int, y=int)
    Write = Variant(str)
    ChangeColor = Variant(int, int, int)
    Pause = Variant()


def test_miscs():
    with pytest.raises(NotAllowedError):
        Message()


def test_relationship():
    # Unit cases are the instances. Use fieldless case if you want issubclass work.
    assert isinstance(Message.Quit, Message)

    assert issubclass(Message.Move, Message)
    assert isinstance(Message.Write("hello"), Message.Write)
    assert isinstance(Message.Write("hello"), Message)
    assert isinstance(Message.Move(x=123, y="hello"), Message.Move)
    assert isinstance(Message.Move(x=123, y="hello"), Message)
    assert isinstance(Message.ChangeColor(123, 456, 789), Message.ChangeColor)
    assert isinstance(Message.ChangeColor(123, 456, 789), Message)
    assert isinstance(Message.Pause(), Message.Pause)
    assert isinstance(Message.Pause(), Message)


def test_instancing_and_runtime_check():
    type MyTypeAlias = int | str | bytes

    @fieldenum(runtime_check=True)
    class Message[T]:
        Quit = Unit
        Move = Variant(x=int, y=int)
        Write = Variant(str)
        ChangeColor = Variant(int | str, T, Any)
        Pause = Variant()
        UseTypeAlias = Variant(MyTypeAlias)
        UseSelf = Variant(Self)

    Message.Move(x=123, y=567)
    Message.Write("hello, world!")
    Message.ChangeColor("hello", (), 123)
    Message.ChangeColor(1234, [], b"bytes")
    Message.Pause()

    with pytest.raises(TypeError):
        Message.Move(x=1234)  # incomplete
    with pytest.raises(TypeError):
        Message.Move(x=1234, y="hello")
    with pytest.raises(TypeError):
        Message.Move(x="hello", y="world")
    with pytest.raises(TypeError):
        Message.Write([])
    with pytest.raises(TypeError):
        Message.ChangeColor((), 1343, 1234)
    with pytest.raises(TypeError):
        Message.Pause(1234)
    with pytest.raises(TypeError):
        Message.Write(x=2)
    with pytest.raises(TypeError):
        Message.Move(123)


def test_eq_and_hash():
    assert Message.ChangeColor(1, ("hello",), [1, 2, 3]) == Message.ChangeColor(1, ("hello",), [1, 2, 3])
    myset = {
        Message.ChangeColor(1, ("hello",), (1, 2, 3)),
        Message.Quit,
        Message.Move(x=234, y=(2, "hello")),
        Message.Pause(),
    }
    assert Message.ChangeColor(1, ("hello",), (1, 2, 3)) in myset
    assert Message.Quit in myset
    assert Message.Move(x=234, y=(2, "hello")) in myset
    assert Message.Pause() in myset

    myset.add(Message.ChangeColor(1, ("hello",), (1, 2, 3)))
    myset.add(Message.Quit)
    myset.add(Message.Move(x=234, y=(2, "hello")))
    myset.add(Message.Pause())
    assert len(myset) == 4


@pytest.mark.parametrize(
    "message",
    [
        Message.Move(x=123, y=456),
        Message.ChangeColor(1, 2, 3),
        Message.Pause(),
        Message.Write("hello"),
        Message.Quit,
    ],
)
def test_pickling(message):
    dump = pickle.dumps(message)
    load = pickle.loads(dump)
    assert message == load


def test_complex_matching():
    match Message.Move(x=123, y=456):
        case Message.Write("hello"):
            assert False

        case Message.Move(x=_, y=123):
            assert False

        case Message.Move(x=_, y=1 | 456):
            assert True

        case _:
            assert False


@pytest.mark.parametrize(
    "message,expect",
    [
        (Message.Move(x=123, y=456), ("move", 456)),
        (Message.ChangeColor(1, 2, 3), ("color", 1, 2, 3)),
        (Message.Pause(), "fieldless"),
        (Message.Write("hello"), ("write", "hello")),
        (Message.Quit, "quit"),
    ],
)
def test_simple_matching(message, expect):
    match message:
        case Message.ChangeColor(x, y, z):
            assert expect == ("color", x, y, z)

        case Message.Quit:
            assert expect == "quit"

        case Message.Pause():
            assert expect == "fieldless"

        case Message.Write(msg):
            assert expect == ("write", msg)

        case Message.Move(x=123, y=y):
            assert expect == ("move", y)

    # don't do these
    match message:
        case Message.ChangeColor(x, y):
            assert expect[0] == "color"

        case Message.Write():
            assert expect[0] == "write"

        case Message.Move():
            assert expect[0] == "move"


def test_repr():
    assert repr(Message.Quit) == "Message.Quit"
    assert repr(Message.Move(x=123, y=234)) == "Message.Move(x=123, y=234)"
    assert repr(Message.Write("hello!")) == "Message.Write('hello!')"
    assert repr(Message.ChangeColor(123, 456, 789)) == "Message.ChangeColor(123, 456, 789)"
    assert repr(Message.Pause()) == "Message.Pause()"
