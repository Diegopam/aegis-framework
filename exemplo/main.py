#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote
import urllib.request
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, GLib


def log(msg):
    print(f"[RaijinForge] {msg}")


def detectar_distro():
    try:
        with open("/etc/os-release") as f:
            for linha in f:
                if linha.startswith("ID="):
                    return linha.strip().split("=")[1].replace('"', '')
    except:
        return "desconhecido"


def dependencias_ok():
    try:
        gi.require_version('WebKit2', '4.0')
        from gi.repository import WebKit2, Gtk
        return True
    except (ImportError, ValueError):
        return False


def instalar_dependencias():
    distro = detectar_distro()
    log(f"Distro detectada: {distro}")

    pacotes_comuns = {
        "ubuntu": "python3-gi gir1.2-webkit2-4.0 gstreamer1.0-plugins-good gstreamer1.0-libav",
        "debian": "python3-gi gir1.2-webkit2-4.0 gstreamer1.0-plugins-good gstreamer1.0-libav",
        "linuxmint": "python3-gi gir1.2-webkit2-4.0 gstreamer1.0-plugins-good gstreamer1.0-libav",
        "arch": "python-gobject webkit2gtk gstreamer gst-plugins-good gst-libav",
        "manjaro": "python-gobject webkit2gtk gstreamer gst-plugins-good gst-libav",
        "fedora": "python3-gobject webkit2gtk4 gstreamer1-plugins-good gstreamer1-libav"
    }

    if distro not in pacotes_comuns:
        log(f"Distro não suportada para instalação automática: {distro}")
        return False

    comando = ""
    if distro in ["ubuntu", "debian", "linuxmint"]:
        comando = f"sudo apt update && sudo apt install -y {pacotes_comuns[distro]}"
    elif distro in ["arch", "manjaro"]:
        comando = f"sudo pacman -Syu --noconfirm {pacotes_comuns[distro]}"
    elif distro in ["fedora"]:
        comando = f"sudo dnf install -y {pacotes_comuns[distro]}"

    try:
        log("Iniciando a instalação de dependências...")
        subprocess.run(["pkexec", "bash", "-c", comando], check=True)
        log("Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Erro ao instalar dependências: {e}")
        return False
    except FileNotFoundError:
        log("pkexec não encontrado. Execute o comando manualmente.")
        return False


class RaijinWindow(Gtk.Window):
    def __init__(self, url):
        super().__init__(title="RaijinForge Browser")
        self.set_default_size(1280, 800)
        self.url = url
        self.webview = self.criar_webview()
        self.add(self.webview)
        self.show_all()
        self.connect("destroy", Gtk.main_quit)

    def criar_webview(self):
        context = WebKit2.WebContext.get_default()
        cookie_manager = context.get_cookie_manager()
        cookie_path = str(Path.home() / ".raijinforge_cookies")
        cookie_manager.set_persistent_storage(cookie_path, WebKit2.CookiePersistentStorage.TEXT)

        settings = WebKit2.Settings()
        settings.set_enable_javascript(True)
        settings.set_enable_webgl(True)
        settings.set_enable_webaudio(True)
        settings.set_enable_media(True)
        settings.set_enable_fullscreen(True)
        settings.set_enable_developer_extras(True)
        settings.set_zoom_text_only(False)
        settings.set_enable_site_specific_quirks(True)

        # Flags experimentais
        try:
            settings.set_property("enable-experimental-web-features", True)
            settings.set_property("enable-file-access-api", True)
        except Exception as e:
            log(f"Não foi possível ativar flags experimentais: {e}")

        settings.set_user_agent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )

        webview = WebKit2.WebView.new_with_context(context)
        webview.set_settings(settings)
        webview.set_zoom_level(1.0)

        context.connect("download-started", self.on_download_started)
        webview.connect("decide-policy", self.on_decide_policy)
        webview.connect("permission-request", self.on_permission_request)

        webview.load_uri(self.url)
        return webview

    def limpar_nome(self, uri):
        # Para blob, vamos sugerir um nome padrão
        if uri.startswith("blob:"):
            return "arquivo_blob"
        nome = Path(urlparse(uri).path).name
        nome = unquote(nome.split("?")[0])
        return nome if nome else "arquivo"

    def on_decide_policy(self, webview, decision, decision_type):
        from gi.repository import WebKit2
        if decision_type == WebKit2.PolicyDecisionType.RESPONSE:
            response = decision.get_response()
            # Se for anexo ou mime diferente de html, tentamos controlar download
            if response.is_content_disposition_attachment() or response.get_mime_type() != "text/html":
                uri = response.get_uri()
                decision.ignore()
                GLib.idle_add(self.baixar_manual, uri)
                return True
        return False

    def on_download_started(self, context, download):
        uri = download.get_request().get_uri()

        # Se for blob, não cancelar, pede salvar local e passa para WebKit fazer download
        if uri.startswith("blob:"):
            # Mostra diálogo pra escolher destino
            file_path = self.escolher_destino_blob()
            if file_path:
                download.set_destination(f"file://{file_path}")
                log(f"Salvando blob em {file_path}")
                download.connect("finished", lambda d, w=self: self.log_download_finalizado(d))
                download.connect("failed", lambda d, err, w=self: self.log_download_falhou(d, err))
                # Deixa WebKit controlar o download
            else:
                log("Salvamento blob cancelado pelo usuário.")
                download.cancel()
        else:
            # Cancelamos o download automático e fazemos manualmente
            download.cancel()
            GLib.idle_add(self.baixar_manual, uri)

    def escolher_destino_blob(self):
        dialog = Gtk.FileChooserDialog(
            title="Salvar arquivo (blob) como",
            action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )
        dialog.set_current_name("arquivo_blob")
        response = dialog.run()
        file_path = None
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
        dialog.destroy()
        return file_path

    def baixar_manual(self, uri):
        suggested_name = self.limpar_nome(uri)
        dialog = Gtk.FileChooserDialog(
            title="Salvar arquivo",
            action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )
        dialog.set_current_name(suggested_name)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            log(f"Baixando manualmente: {uri} → {file_path}")
            threading.Thread(target=self._download_thread, args=(uri, file_path), daemon=True).start()
        else:
            log("Download manual cancelado pelo usuário.")
        dialog.destroy()

    def _download_thread(self, uri, file_path):
        try:
            urllib.request.urlretrieve(uri, file_path, self._progresso(file_path))
            log(f"Download concluído: {file_path}")
        except Exception as e:
            log(f"Erro no download: {e}")

    def _progresso(self, file_path):
        def report(block_num, block_size, total_size):
            baixado = block_num * block_size
            if total_size > 0:
                pct = baixado / total_size
                sys.stdout.write(f"\r[Baixando] {file_path} - {pct:.0%}")
                sys.stdout.flush()
        return report

    def log_download_finalizado(self, download):
        log(f"Download blob finalizado: {download.get_destination_uri()}")

    def log_download_falhou(self, download, error):
        log(f"Download blob falhou: {download.get_request().get_uri()} - {error.message}")

    def on_permission_request(self, webview, request):
        log(f"Pedido de permissão: {type(request)}")
        try:
            request.allow()
        except:
            request.deny()
        return True


if __name__ == "__main__":
    if not dependencias_ok():
        log("Dependências ausentes. Tentando instalar...")
        if not instalar_dependencias():
            sys.exit(1)

    link = "https://www.olhosnatv.com.br"
    RaijinWindow(link)
    Gtk.main()
