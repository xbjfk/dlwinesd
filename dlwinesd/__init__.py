import hashlib
import tempfile
import requests
import subprocess
import xmltodict

import sys


class NoSuchMatchException(Exception):
    def __init__(self, matchtype, matchconds):
        super().__init__(f"No such {matchtype} with conditions {matchconds}.")


class AmbiguousMatchException(Exception):
    def __init__(self, matchtype, matchedprods, matchconds):
        msg = f"Multiple Windows {matchtype} were matched with {matchconds}."
        for i in range(len(matchedprods)):
            msg += f"\nMatch {i}:"
            for item in matchedprods[i].items():
                msg += "\n\t" + str(item)

        super().__init__(msg)
    pass


class WinESD:
    fwlinks = {
        10: "https://go.microsoft.com/fwlink?LinkId=841361",
        11: "https://go.microsoft.com/fwlink?linkid=2156292"
    }
    ver: int = None
    products: str = None
    product = None

    def __init__(self, ver):
        self.ver = ver

    def update_products(self):
        if self.products:
            return self.products
        else:
            r = requests.get(self.fwlinks[self.ver])
            cabfile = tempfile.NamedTemporaryFile()
            cabfile.write(r.content)
            p = subprocess.Popen(["cabextract", "--pipe", "--filter", "products.xml", cabfile.name], stdout=subprocess.PIPE)
            prodxml = p.stdout.read()
            products = xmltodict.parse(prodxml)
            products = products["MCT"]["Catalogs"]["Catalog"]["PublishedMedia"]
            self.products = products

    def set_product(self, edition, arch, lang):
        if self.products is None:
            raise ValueError("self.products is none! Call update_products()")

        product = [file for file in self.products["Files"]["File"] if
                        file["Edition"] == edition
                        and file["Architecture"] == arch
                        and file["LanguageCode"] == lang]

        if len(product) < 1:
            raise NoSuchMatchException("Windows ESD", f"edition: {edition}, arch: {arch} and lang: {lang}")
        elif len(product) > 1:
            raise AmbiguousMatchException("Windows ESDs", product, f"edition: {edition}, arch: {arch} and lang: {lang}")

        self.product = product[0]

    def get_eula(self, lang: str):
        if self.products is None:
            raise ValueError("self.products is none! Call update_products()")

        eula = [eula for eula in self.products["EULAs"]["EULA"] if
                eula["LanguageCode"] == lang]

        if len(eula) != 1:
            raise AmbiguousMatchException("Windows EULAs", eula, f"lang: {lang}")

        eula = eula[0]
        url = eula["URL"]

        return url

    def get_url(self):
        if self.product is None:
            raise ValueError("self.product is none! Call set_product()")

        return self.product["FilePath"]

    def download(self, outfile=None):
        if self.product is None:
            raise ValueError("self.product is none! Call set_product()")

        url = self.product["FilePath"]
        name = self.product["FileName"]

        with requests.get(url, stream=True) as r:
            if outfile is None:
                outfile = open(name, 'wb')

            with outfile:
                bytes_written = 0
                m = hashlib.sha1()
                size = int(self.product["Size"])
                for chunk in r.iter_content(chunk_size=65535):
                    bytes_written += outfile.write(chunk)
                    m.update(chunk)
                    print("\r{:.0f}%".format(100 * (bytes_written / size)), end="")

                assert bytes_written == size
                assert m.hexdigest() == self.product["Sha1"].lower()
                print("\nDone! Saved to", outfile.name)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Download a Windows 10 or 11 ESD directly from Microsoft.')
    parser.add_argument("-o", "--output", type=argparse.FileType('wb'), help="Output file or directory.")
    parser.add_argument("--accept_eula", default=False, action='store_true', help="Accept the Microsoft Windows EULA.")
    parser.add_argument("--get_eula", default=False, action='store_true', help="Get the URL to the EULA.")
    parser.add_argument("--get_url", default=False, action='store_true', help="Do not attempt to download, only print URL.")
    parser.add_argument("release", type=int, help="Which Windows release to download. Currently 10 and 11 are supported.")
    parser.add_argument("edition", type=str, help="Which Windows edition to download. Set to list to list editions.")
    parser.add_argument("arch", type=str, help="Which Windows architecture to download. Set to list to list architectures.")
    parser.add_argument("lang", type=str, help="Which Windows language to download. Set to list to list language codes.")

    args = parser.parse_args()
    rel = args.release

    if rel not in WinESD.fwlinks.keys():
        print("The selected Windows release is invalid!", file=sys.stderr)
        exit(1)

    if not any([args.accept_eula, args.get_eula]):
        print("You must accept the Windows EULA! Rerun with --get_eula or --accept_eula", file=sys.stderr)
        exit(1)

    esd = WinESD(rel)

    esd.update_products()

    if args.get_eula:
        print("The EULA is downloadable from:", esd.get_eula(args.lang))
        exit(0)

    esd.set_product(args.edition, args.arch, args.lang)

    if args.get_url:
        print(esd.get_url())
    else:
        esd.download()


if __name__ == "__main__":
    main()
