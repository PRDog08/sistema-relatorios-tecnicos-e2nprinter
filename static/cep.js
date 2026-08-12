(() => {
    const campoCep = document.querySelector('input[name="cep"]');

    if (!campoCep) {
        return;
    }

    const status = document.createElement("small");
    status.className = "ajuda-campo cep-status";
    status.setAttribute("aria-live", "polite");
    campoCep.insertAdjacentElement("afterend", status);

    let ultimoCepConsultado = "";
    let consultaEmAndamento = false;

    function somenteNumeros(valor) {
        return valor.replace(/\D/g, "").slice(0, 8);
    }

    function formatarCep(valor) {
        const cep = somenteNumeros(valor);
        return cep.length > 5 ? `${cep.slice(0, 5)}-${cep.slice(5)}` : cep;
    }

    function preencherCampo(nome, valor) {
        const campo = document.querySelector(`[name="${nome}"]`);
        if (campo) {
            campo.value = valor || "";
        }
    }

    async function consultarCep() {
        const cep = somenteNumeros(campoCep.value);

        if (cep.length !== 8 || cep === ultimoCepConsultado || consultaEmAndamento) {
            return;
        }

        ultimoCepConsultado = cep;
        consultaEmAndamento = true;
        status.textContent = "Buscando endereco...";

        try {
            const resposta = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            if (!resposta.ok) {
                throw new Error("Falha ao consultar o CEP.");
            }

            const dados = await resposta.json();
            if (dados.erro) {
                status.textContent = "CEP nao encontrado.";
                return;
            }

            preencherCampo("endereco", dados.logradouro);
            preencherCampo("bairro", dados.bairro);
            preencherCampo("cidade", dados.localidade);
            preencherCampo("uf", dados.uf);
            status.textContent = "Endereco preenchido automaticamente.";
        } catch (erro) {
            console.error(erro);
            status.textContent = "Nao foi possivel consultar o CEP agora.";
        } finally {
            consultaEmAndamento = false;
        }
    }

    campoCep.value = formatarCep(campoCep.value);
    campoCep.addEventListener("input", () => {
        campoCep.value = formatarCep(campoCep.value);
        status.textContent = "";
        ultimoCepConsultado = "";
        consultarCep();
    });

    campoCep.addEventListener("blur", consultarCep);
})();
