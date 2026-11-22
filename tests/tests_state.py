import state


def test_save_and_load_roundtrip(fake_state_file):
    """Что сохранили — то и загрузили."""
    state.save_state(1234567890.5)
    assert state.load_state() == 1234567890.5


def test_load_when_no_file(fake_state_file):
    """Если файла нет — возвращаем None, не падаем."""
    assert not fake_state_file.exists()
    assert state.load_state() is None


def test_load_corrupted_file(fake_state_file):
    """Если в файле мусор — возвращаем None и удаляем файл."""
    fake_state_file.write_text("не число", encoding="utf-8")

    assert state.load_state() is None
    assert not fake_state_file.exists()  # повреждённый файл удалён


def test_save_zero_does_nothing(fake_state_file):
    """0 — это «нет таймера», файл не создаём."""
    state.save_state(0)
    assert not fake_state_file.exists()


def test_clear_state(fake_state_file):
    """clear_state удаляет файл."""
    state.save_state(1000.0)
    assert fake_state_file.exists()

    state.clear_state()
    assert not fake_state_file.exists()


def test_clear_when_no_file_does_not_raise(fake_state_file):
    """clear_state не падает, если файла нет."""
    state.clear_state() 