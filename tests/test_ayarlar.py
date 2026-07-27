import unittest

from ayarlar import ARAC_SINIFLARI


class AyarlarTestleri(unittest.TestCase):

    def test_arac_siniflari_tarife_listesiyle_ayni(self):
        self.assertEqual(
            ARAC_SINIFLARI,
            [
                "Motosiklet",
                "Çapa",
                "Otomobil",
                "Toplu Taşıma",
                "Traktör Römorklu",
                "Kamyonet",
                "Kamyon",
                "Uzun Araç"
            ]
        )


if __name__ == "__main__":
    unittest.main()
