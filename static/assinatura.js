(() => {
    const canvas = document.getElementById("assinatura-cliente-canvas");
    const dados = document.getElementById("assinatura-cliente-dados");
    const limpar = document.getElementById("limpar-assinatura");
    const status = document.getElementById("assinatura-cliente-status");
    const formulario = canvas?.closest("form");

    if (!canvas || !dados || !limpar || !status || !formulario) return;

    const contexto = canvas.getContext("2d");
    let escala = window.devicePixelRatio || 1;
    let assinaturaEditada = false;
    let desenhoAtual = false;
    let ponteiroAtivo = false;

    function tamanhoCanvas() {
        const retangulo = canvas.getBoundingClientRect();
        const imagemExistente = dados.value;
        escala = window.devicePixelRatio || 1;
        canvas.width = Math.max(1, Math.round(retangulo.width * escala));
        canvas.height = Math.max(1, Math.round(retangulo.height * escala));
        contexto.setTransform(escala, 0, 0, escala, 0, 0);
        contexto.lineWidth = 2.5;
        contexto.lineCap = "round";
        contexto.lineJoin = "round";
        contexto.strokeStyle = "#17212b";

        if (imagemExistente) {
            const imagem = new Image();
            imagem.onload = () => {
                contexto.drawImage(imagem, 0, 0, retangulo.width, retangulo.height);
            };
            imagem.src = imagemExistente;
        }
    }

    function ponto(evento) {
        const retangulo = canvas.getBoundingClientRect();
        return { x: evento.clientX - retangulo.left, y: evento.clientY - retangulo.top };
    }

    canvas.addEventListener("pointerdown", (evento) => {
        evento.preventDefault();
        if (!assinaturaEditada) {
            contexto.clearRect(0, 0, canvas.width / escala, canvas.height / escala);
            assinaturaEditada = true;
            dados.value = "";
        }
        ponteiroAtivo = true;
        desenhoAtual = false;
        canvas.setPointerCapture(evento.pointerId);
        const { x, y } = ponto(evento);
        contexto.beginPath();
        contexto.moveTo(x, y);
        status.textContent = "Solte o quadro quando terminar de assinar.";
    });

    canvas.addEventListener("pointermove", (evento) => {
        if (!ponteiroAtivo) return;
        evento.preventDefault();
        const { x, y } = ponto(evento);
        contexto.lineTo(x, y);
        contexto.stroke();
        desenhoAtual = true;
    });

    function finalizarTraco() {
        if (!ponteiroAtivo) return;
        ponteiroAtivo = false;
        if (desenhoAtual) {
            dados.value = canvas.toDataURL("image/png");
            status.textContent = "Assinatura pronta para salvar no relatório.";
        } else {
            status.textContent = "O quadro ficou vazio. Assine usando o dedo ou a caneta.";
        }
    }

    canvas.addEventListener("pointerup", finalizarTraco);
    canvas.addEventListener("pointercancel", finalizarTraco);

    limpar.addEventListener("click", () => {
        contexto.clearRect(0, 0, canvas.width / escala, canvas.height / escala);
        dados.value = "";
        assinaturaEditada = true;
        desenhoAtual = false;
        status.textContent = "Assinatura removida. Você pode assinar novamente.";
    });

    formulario.addEventListener("submit", () => {
        if (ponteiroAtivo) finalizarTraco();
    });

    if (dados.value) {
        status.textContent = "Assinatura salva. Assine novamente no quadro para substituí-la.";
    }

    tamanhoCanvas();
    if ("ResizeObserver" in window) {
        new ResizeObserver(() => tamanhoCanvas()).observe(canvas);
    } else {
        window.addEventListener("resize", tamanhoCanvas);
    }
})();
