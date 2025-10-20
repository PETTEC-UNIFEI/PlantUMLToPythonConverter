// --- Elementos da DOM ---
const plantUmlInput = document.getElementById('plantUmlInput');
const codeOutput = document.getElementById('codeOutput');
const outputTitle = document.getElementById('outputTitle');
const languageSelect = document.getElementById('languageSelect');
const convertBtn = document.getElementById('convertBtn');
const copyBtn = document.getElementById('copyBtn');
const clearBtn = document.getElementById('clearBtn');
const importBtn = document.getElementById('importBtn');
const historyBtn = document.getElementById('historyBtn');

// Atualiza o título do painel de saída baseado na linguagem selecionada
function updateOutputTitle() {
    const language = languageSelect.value;
    const languageNames = {
        'python': 'Código Python',
        'csharp': 'Código C#'
    };
    outputTitle.textContent = languageNames[language] || 'Código Gerado';
}

// Event listener para mudança de linguagem
languageSelect.addEventListener('change', updateOutputTitle);

// Inicializa o título
updateOutputTitle();

// Exemplo de código PlantUML para iniciar
// plantUmlInput.value = `@startuml
// class Person {
//   -name: str
//   -age: int
//   +Person(name: str, age: int)
//   +greet() -> str
// }

// class Student extends Person {
//   -student_id: str
//   +study()
// }
// @enduml`;
// O campo começa vazio para exibir o placeholder

// --- Event Listeners ---

// Botão de Conversão (Integração com PyWebView)
convertBtn.addEventListener('click', async () => {
    const plantUmlCode = plantUmlInput.value;
    const selectedLanguage = languageSelect.value;
    codeOutput.innerHTML = '<span class="text-yellow-400">Convertendo...</span>';

    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        codeOutput.innerHTML = '<span class="text-red-500 font-semibold">Erro: A comunicação com o backend (PyWebView) não está disponível. Rode o app a partir do script Python.</span>';
        return;
    }

    try {
        const result = await window.pywebview.api.convert_plantuml(plantUmlCode, selectedLanguage);
        if (!result || typeof result !== 'string' || result.startsWith('Erro')) {
            codeOutput.innerHTML = `<span class="text-red-500 font-semibold">${result || 'Erro ao converter o diagrama.'}</span>`;
            return;
        }
        // A resposta agora é o caminho para o diretório
        renderFileExplorer(result);
    } catch (err) {
        codeOutput.textContent = 'Erro ao comunicar com o backend: ' + err;
        codeOutput.classList.add('text-red-500');
    }
});

// Função para renderizar o explorador de arquivos
async function renderFileExplorer(dirPath) {
    window._lastExplorerDir = dirPath; // Salva o último diretório para o botão "voltar"
    codeOutput.innerHTML = '<span class="text-yellow-400">Carregando arquivos...</span>';
    try {
        let entries = await window.pywebview.api.list_dir(dirPath);
        codeOutput.innerHTML = '';
        // DEBUG: Mostra o caminho do diretório atual no topo do explorador
        const dirInfo = document.createElement('div');
        dirInfo.className = 'text-xs text-gray-400 mb-2 select-all';
        dirInfo.textContent = `Diretório: ${dirPath}`;
        codeOutput.appendChild(dirInfo);
        if (!entries || entries.length === 0 || (entries.every(e => e.error))) {
            codeOutput.innerHTML += '<span class="text-red-400">Nenhum código gerado para este diagrama.</span>';
            return;
        }
        const explorer = document.createElement('div');
        explorer.className = 'file-explorer';
        buildExplorerTree(explorer, entries);
        codeOutput.appendChild(explorer);
    } catch (e) {
        codeOutput.innerHTML = `<span class="text-red-500">Erro ao listar diretório: ${e}</span>`;
    }
}

// Função recursiva para montar a árvore de arquivos
function buildExplorerTree(container, entries) {
    const ul = document.createElement('ul');
    ul.className = 'pl-2';
    entries.forEach(entry => {
        const li = document.createElement('li');
        li.className = 'mb-1';
        const fullPath = entry.path;

        if (entry.is_dir) {
            li.innerHTML = `<span class="cursor-pointer text-blue-400 hover:underline flex items-center gap-2">📁 ${entry.name}</span>`;
            li.onclick = async (e) => {
                e.stopPropagation();
                try {
                    const subEntries = await window.pywebview.api.list_dir(fullPath);
                    li.onclick = null;
                    li.querySelector('span').innerHTML = `📂 ${entry.name}`;
                    buildExplorerTree(li, subEntries);
                } catch (err) {
                    console.error("Erro ao expandir diretório:", err);
                }
            };
        } else {
            li.innerHTML = `<span class="cursor-pointer text-green-400 hover:underline flex items-center gap-2">📄 ${entry.name}</span>`;
            li.onclick = async (e) => {
                e.stopPropagation();
                try {
                    const content = await window.pywebview.api.read_file(fullPath);
                    showFileContent(entry.name, content);
                } catch (err) {
                    console.error("Erro ao ler arquivo:", err);
                }
            };
        }
        ul.appendChild(li);
    });
    container.appendChild(ul);
}

// Função para exibir o conteúdo do arquivo
function showFileContent(filename, content) {
    codeOutput.innerHTML = '';
    const wrapper = document.createElement('div');
    wrapper.className = 'relative h-full flex flex-col';

    const header = document.createElement('div');
    header.className = 'flex items-center p-2 border-b border-gray-700';

    const backBtn = document.createElement('button');
    backBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>';
    backBtn.className = 'bg-blue-600 hover:bg-blue-700 rounded-full p-1.5 text-white shadow-lg transition-colors';
    backBtn.title = 'Voltar para o diretório';
    backBtn.onclick = () => {
        if (window._lastExplorerDir) {
            renderFileExplorer(window._lastExplorerDir);
        }
    };
    header.appendChild(backBtn);

    const fileTitle = document.createElement('div');
    fileTitle.className = 'ml-4 font-semibold text-blue-300';
    fileTitle.textContent = filename;
    header.appendChild(fileTitle);

    wrapper.appendChild(header);

    const pre = document.createElement('pre');
    pre.className = 'flex-grow bg-gray-900 p-3 overflow-auto text-sm';
    const code = document.createElement('code');
    
    // Determina a linguagem de syntax highlighting baseada na extensão do arquivo
    if (filename.endsWith('.py')) {
        code.className = 'language-python';
    } else if (filename.endsWith('.cs')) {
        code.className = 'language-csharp';
    } else {
        code.className = 'language-text';
    }
    
    code.textContent = content;
    pre.appendChild(code);
    wrapper.appendChild(pre);

    codeOutput.appendChild(wrapper);
}

// Botão de Limpar
clearBtn.addEventListener('click', () => {
    plantUmlInput.value = '';
    codeOutput.innerHTML = '<code id="codeOutput" class="text-sm font-mono text-gray-300"># O código gerado aparecerá aqui...</code>';
    plantUmlInput.focus();
});

// Botão de Copiar (Copia o conteúdo visível na área de saída)
copyBtn.addEventListener('click', () => {
    const codeToCopy = codeOutput.textContent;
    const textArea = document.createElement('textarea');
    textArea.value = codeToCopy;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 mr-2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg> Copiado!';
    } catch (err) {
        console.error('Falha ao copiar texto: ', err);
        copyBtn.textContent = 'Erro';
    }
    document.body.removeChild(textArea);

    setTimeout(() => {
        copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 mr-2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.03 1.125 0 1.131.094 1.976 1.057 1.976 2.192V7.5m-9 3c0-1.135.845-2.098 1.976-2.192a48.424 48.424 0 011.125 0c1.131.094 1.976 1.057 1.976 2.192V18a2.25 2.25 0 002.25 2.25h3.375c1.24 0 2.25-1.01 2.25-2.25V10.5c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.125 0c-1.131.094-1.976-1.057-1.976-2.192V7.5" /></svg> Copiar';
    }, 2000);
});

// Botão de Importar Arquivo
importBtn.addEventListener('click', () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.puml,.plantuml,.wsd,.txt,*/*';
    fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (evt) => {
            plantUmlInput.value = evt.target.result;
        };
        reader.readAsText(file, 'utf-8');
    };
    fileInput.click();
});

// Botão de Histórico: mostra o conteúdo de output_generated_code
historyBtn.addEventListener('click', async () => {
    if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
        codeOutput.innerHTML = '<span class="text-red-500 font-semibold">Erro: A comunicação com o backend (PyWebView) não está disponível. Rode o app a partir do script Python.</span>';
        return;
    }
    codeOutput.innerHTML = '<span class="text-yellow-400">Carregando histórico...</span>';
    try {
        // Caminho relativo ao backend
        let result = await window.pywebview.api.list_dir('data/output_generated_code');
        // Ordena alfabeticamente e numericamente
        result = result.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
        codeOutput.innerHTML = '';
        const explorer = document.createElement('div');
        explorer.className = 'file-explorer';
        buildExplorerTree(explorer, result);
        codeOutput.appendChild(explorer);
    } catch (e) {
        codeOutput.innerHTML = `<span class="text-red-500">Erro ao acessar histórico: ${e}</span>`;
    }
});
