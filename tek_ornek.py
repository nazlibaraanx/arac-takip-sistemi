import os


class TekOrnekKilidi:
    """Aynı uygulamanın ikinci kopyasının çalışmasını engeller."""

    def __init__(self, kilit_yolu):
        self.kilit_yolu = os.path.abspath(kilit_yolu)
        self.sahip = False

    @staticmethod
    def _surec_calismakta_mi(pid):
        try:
            os.kill(int(pid), 0)
            return True
        except (OSError, ValueError, TypeError):
            return False

    def al(self):
        os.makedirs(os.path.dirname(self.kilit_yolu), exist_ok=True)
        for _ in range(2):
            try:
                tanimlayici = os.open(
                    self.kilit_yolu,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                with os.fdopen(tanimlayici, "w", encoding="ascii") as dosya:
                    dosya.write(str(os.getpid()))
                self.sahip = True
                return True
            except FileExistsError:
                try:
                    with open(
                        self.kilit_yolu, "r", encoding="ascii"
                    ) as dosya:
                        mevcut_pid = dosya.read().strip()
                except OSError:
                    return False
                if self._surec_calismakta_mi(mevcut_pid):
                    return False
                try:
                    os.remove(self.kilit_yolu)
                except OSError:
                    return False
        return False

    def birak(self):
        if not self.sahip:
            return
        try:
            os.remove(self.kilit_yolu)
        except FileNotFoundError:
            pass
        finally:
            self.sahip = False
