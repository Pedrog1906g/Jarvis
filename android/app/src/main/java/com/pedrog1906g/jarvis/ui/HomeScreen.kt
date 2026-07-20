// Mudanças propostas:
// 1. Adicione um botão de loading para indicar quando a aplicação está carregando dados
// 2. Melhore a experiência de usuário ao exibir uma mensagem de erro personalizada
// 3. Adicione uma opção de notificação para o usuário quando houver novas atualizações disponíveis

@Composable
fun HomeScreen(
    viewModel: HomeViewModel = viewModel(),
    navigateToSettings: () -> Unit = {}
) {
    val state = viewModel.state

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Botão de loading
        if (state.isLoading) {
            CircularProgressIndicator()
        }

        // Exibir mensagem de erro personalizada
        if (state.hasError) {
            Text(
                text = "Erro ao carregar dados. Por favor, tente novamente.",
                color = MaterialTheme.colors.error
            )
        }

        // Opção de notificação para novas atualizações
        if (state.hasUpdateAvailable) {
            Text(
                text = "Nova atualização disponível! Atualize para aproveitar novas funcionalidades.",
                color = MaterialTheme.colors.primary
            )
        }

        // Restante da tela
        // ...
    }
}