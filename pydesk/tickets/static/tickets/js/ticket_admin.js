document.addEventListener('DOMContentLoaded', function() {
    const estadoSelect = document.querySelector('#id_estado'); // ID padrão gerado pelo Django para o campo estado
    
    // Seleciona os blocos/divs que envolvem os campos no Django Admin
    const fieldSolucao = document.querySelector('.field-solucao');
    const fieldCancelamento = document.querySelector('.field-motivo_cancelamento');
    const fieldDataEncerramento = document.querySelector('.field-data_encerramento');

    function atualizarVisibilidade() {
        if (!estadoSelect) return;
        
        const valorEstado = estadoSelect.value;

        // Oculta ambos por padrão
        if (fieldSolucao) fieldSolucao.style.display = 'none';
        if (fieldCancelamento) fieldCancelamento.style.display = 'none';
        if (fieldDataEncerramento) fieldDataEncerramento.style.display = 'none';

        // Mostra o campo correspondente com base no valor selecionado
        // (Substitua 'ENC' e 'CAN' pelas siglas reais do seu TextChoices de Estado)
        if (valorEstado === 'EN') { 
            if (fieldSolucao) {
                fieldSolucao.style.display = 'block';
                fieldDataEncerramento.style.display = 'block';
            }
        } else if (valorEstado === 'CC') {
            if (fieldCancelamento) {
                fieldCancelamento.style.display = 'block';
                fieldDataEncerramento.style.display = 'block';
            }
        }
    }

    if (estadoSelect) {
        // Executa ao carregar a página
        atualizarVisibilidade();
        // Executa sempre que o usuário mudar a opção no dropdown
        estadoSelect.addEventListener('change', atualizarVisibilidade);
    }
});