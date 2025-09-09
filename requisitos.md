Coisas a fazer no programa:

1- Editar Referências -- feito

2- Tabelas -- feito

3- Mover os tópicos de lugar(para cima ou para baixo na aba de conteúdo) -- feito

4- Adicionar Imagens, inclusive em diferentes formatos(JPG, PNG, WEBP, etc) -- Feito

5- Sistema de prévias dentro do programa

6- Opção de mover tópicos de lugar, seja uma ferramenta onde o usuário ativa
e desativa, para evitar mover acidentalmente um tópico -- feito

7- Criar, salvar e carregar projetos. Por exemplo um usuário pode criar mais de um projeto
salvar eles e carregar os que tão salvos, inclusive podendo compartilhar o arquivo de salvamento
com outros usuários para eles carregarem o projeto na máquina deles. Vamos ver
a viabilidade de criarmos um formato nosso próprio de arquivo, esse formato de arquivo
vai armazenar dados e imagens dentro dele como se fosse uma pasta, semelhante ao que o PSD do photoshop faz.
Obs: o nome de extensão usado será o .abnf -- feito

8- Deve ter a possibilidade de adicionar um titulo ao projeto. -- pedente, estou pensando se implemento

8- O banco de tabelas e o banco de figuras deve ser "global" para o projeto, atualmente elas ficam separadas por tópico -- feito

9 - Adicionar o brasão da faculdade e/ou do estado na capa(mas primeiro conferir se as regras ABNT permite)

10- Tela inicial que irá mostrar os últimos projetos salvos, com os botões abrir, novo, carregar. E se o usuário clicar em um dos projetos
que aparece no painel ele irá direto para edição desse projeto. Semelhante ao photoshop e coreldrawn por exemplo. E nessa tela terá a opção do usuario
já iniciar o projeto com o modelo que ele quer, TCC, Tese, etc. Semelhante a tela de escolha de resoluções do photoshop.
obs: Deve ser criado um novo arquivo para essa funcionalidade

Texto reformulado: Agora vamos fazer uma tela inicial que irá mostrar os últimos projetos salvos, com os botões abrir, novo, carregar. E se o usuário clicar em um dos projetos

que aparece no painel ele irá direto para edição desse projeto. Semelhante ao photoshop e coreldrawn por exemplo. E nessa tela terá a opção do usuario

já iniciar o projeto com o modelo que ele quer, TCC, Tese, etc. Semelhante a tela de escolha de resoluções do photoshop. Quando o usuário salvar o projeto o programa irá armazenar o caminho que o projeto foi salvo assim ele pode abrir o projeto pela interface semelhante a que outros programas fazem, caso o usuário mude o projeto de caminho ou apague e tente abrir pela interface o programa vai avisar que o projeto não foi encontrado e ele irá sumir da tela inicial, semelhante ao que os programas profissionais fazem. -- Feito

obs: Deve ser criado um novo arquivo para essa funcionalidade

11- Sistema de backup automatico contra perda de dados e sistema de recuperação de arquivos semelhante ao do corel drawn -- Feito

12- Regra diferente de formatação para artigo cientifico -- Feito

13- Ferramenta de busca na aba de preview -- Feito

14- Quando for selecionado o modelo de artigo, as perguntas da tela inicial devem corresponder ao modelo e não ficar fixo no padrão de tcc, mestrado, doutorado

15- Ferramenta de busca na aba conteudo -- Feito

16- Ter a opção de colocar a aba de prévia aberta direto do lado direito do editor e que ela recarregue automatico a cada modificação do projeto -- Feito, precisa de alguns refinamentos mas está funcional

17- Filtrar imagens e tabelas por tópico nos bancos -- Feito

18- Prévia da imagem no editor de figuras -- Feito

19- Personalização de tipos de fonte e cores dos tópicos na exportação em doc

20- Exportação de PDF direta do programa

21- Impressão Direta do Programa

22- Opção de Voltar a tela inicial para entrar em outro projeto pela interface

23- Na tela inicial adicionar uma opção de criar projeto "guiado"(procurar um nome melhor), para o usuário fazer todas as configurações do projeto de forma muito intuitiva, para usuários leigos, o programa vai fazer perguntas referente ao projeto e o usuário vai responder. Exemplo: "Qual o nome do seu orientador?", "Qual instituição você estuda" e dê um exemplo de como responder. Semelhante a tela de configuração da cortana no windows, onde aparecem os textos com uma animação discreta e intuitiva que seja amigável para o usuário leigo.

Correções:

Quando cria a tabela e ela está sem nome, gera um erro da tabela não poder ser
salva sem nome e a caixa de edição da tabela fecha, isso não deve acontecer
a mensagem de erro deve aparecer e a caixa de edição da tabela deve continuar aberta
para evitar que o usuário perca o conteúdo que estava trabalhando. -- Corrigido

O distanciamento do inicio de paragrafo não está sendo respeitado, conforme as normas ABNT exigem. -- Corrigido

A formatação do arquivo em docx