"""Executa o spinner chat simulando /compare bench_a.pkl bench_b.pkl."""
import sys
import io
import dotenv

dotenv.load_dotenv(".env")

# Registra _DictConfig no __main__ para o pickle encontrar ao desserializar
from make_test_pkls import _DictConfig  # noqa: F401  (needed for pickle)
sys.modules[__name__]._DictConfig = _DictConfig

# Força UTF-8 no stdout (evita UnicodeEncodeError no Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Simula o usuario digitando no terminal interativo
sys.stdin = io.TextIOWrapper(
    io.BytesIO(b"/compare bench_a.pkl bench_b.pkl\nexit\n"),
    encoding="utf-8",
)

from spinner.chat.chat import chat_with_data  # noqa: E402

chat_with_data("bench_a.pkl")
