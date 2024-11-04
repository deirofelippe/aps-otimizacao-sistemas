# -*- coding: utf-8 -*-
"""aps-otimizacao-de-sistemas-2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/15DnPYMFsOGSSUwL3BAXbAA-mhR4om-tI
"""

import numpy as np
import pandas as pd
import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from datetime import datetime, timedelta

## INPUTS

# Lista de tickers dos ativos
tickers = ['AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL']
# tickers = ['AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'NVDA', 'NFLX']

# Nível máximo de risco aceitável (volatilidade)
risk_tolerance = 0.25  # 25% de volatilidade máxima

# Data inicial para coleta de dados (hoje - 365 dias)
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

# Data final para coleta de dados
end_date = datetime.now().strftime('%Y-%m-%d')

def portfolio_performance(mean_returns, cov_matrix, weights):
  """Calcula retorno e risco da carteira"""
  # Retorno da carteira, média ponderada dos retornos individuais
  returns = np.sum(mean_returns * weights)
  # Risco/Volatilidade, raiz quadrada da variância da carteira usando a matriz de covariância
  risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
  return returns, risk

def negative_sharpe_ratio(mean_returns, cov_matrix, weights):
  """Calcula o índice de Sharpe negativo (para minimização)"""
  returns, risk = portfolio_performance(mean_returns, cov_matrix, weights)
  return -returns/risk

def optimize_portfolio(tickers, risk_tolerance, mean_returns, cov_matrix):
  """Otimiza a carteira usando o problema da mochila adaptado"""
  n_assets = len(tickers)

  ineq_function = lambda weights: risk_tolerance - portfolio_performance(mean_returns, cov_matrix, weights)[1]

  constraints = (
      {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Restrição de igualdade
      {'type': 'ineq', 'fun': ineq_function},   # Restrição de desigualdade 
  )

  # limites inferior (0) e superior (1) para cada peso
  bounds = tuple((0, 1) for _ in range(n_assets))      # 0 <= peso <= 1

  # Pesos iniciais iguais
  initial_weights = np.array([1 / n_assets] * n_assets)

  fun = lambda weights: negative_sharpe_ratio(mean_returns, cov_matrix, weights)

  # Otimização
  result = minimize(
      fun, # Função objetivo
      initial_weights, #
      method='SLSQP', # Método de otimização
      bounds=bounds, # Limites das variáveis
      constraints=constraints # Restrições
  )

  optimal_weights = result.x

  return optimal_weights

def fetch_data(tickers, start_date, end_date):
  data = pd.DataFrame()

  for ticker in tickers:
      stock = yf.download(ticker, start=start_date, end=end_date)
      data[ticker] = stock['Adj Close']

  # Calcula a variação percentual entre elementos consecultivos
  returns = data.pct_change().dropna()
  # Calcula a média da variação
  mean_returns = returns.mean() * 252  # Anualizado
  # Calcula a matriz de covariância da variação
  cov_matrix = returns.cov() * 252     # Anualizada

  return data, returns, mean_returns, cov_matrix

print()

# Busca os dados dos ativos
data, returns, mean_returns, cov_matrix = fetch_data(tickers, start_date, end_date)
# Faz a otimização
optimal_weights = optimize_portfolio(tickers=tickers, risk_tolerance=risk_tolerance, cov_matrix=cov_matrix,mean_returns=mean_returns)

def plot_efficient_frontier():
    """Plota a fronteira eficiente"""
    plt.figure(figsize=(10, 6))

    # Gera carteiras aleatórias de exemplo para visualização
    n_portfolios = 1000
    returns = np.zeros(n_portfolios)
    risks = np.zeros(n_portfolios)

    for i in range(n_portfolios):
        weights = np.random.random(len(tickers))
        weights = weights / np.sum(weights)
        returns[i], risks[i] = portfolio_performance(mean_returns, cov_matrix, weights)

    # Plota carteiras aleatórias
    plt.scatter(risks, returns, c='gray', alpha=0.5, label='Carteiras Possíveis')

    # Plota carteira otimizada
    opt_return, opt_risk = portfolio_performance(mean_returns, cov_matrix, optimal_weights)
    plt.scatter(opt_risk, opt_return, c='red', marker='*', s=200, label='Carteira Ótima')

    plt.xlabel('Risco (Volatilidade)')
    plt.ylabel('Retorno Esperado')
    plt.title('Fronteira Eficiente')
    plt.legend()
    plt.show()

def plot_portfolio_allocation():
    """Plota a alocação da carteira otimizada"""
    # Seta o tamanho do gráfico
    plt.figure(figsize=(10, 6))
    # Configura as porcentagens e os ativos de cada porcentagem
    plt.pie(optimal_weights, labels=tickers, autopct='%1.1f%%')
    plt.title('Alocação Ótima da Carteira')
    plt.show()

def plot_performance_evolution():
    """Plota evolução do retorno e risco ao longo do tempo"""
    # Calcula retornos acumulados
    weighted_returns = returns.dot(optimal_weights)
    cumulative_returns = (1 + weighted_returns).cumprod()

    # Calcula volatilidade móvel
    rolling_vol = weighted_returns.rolling(window=21).std() * np.sqrt(252)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # Retornos acumulados
    ax1.plot(cumulative_returns.index, cumulative_returns, label='Retorno Acumulado')
    ax1.set_title('Evolução do Retorno da Carteira')
    ax1.legend()

    # Volatilidade móvel
    ax2.plot(rolling_vol.index, rolling_vol, label='Volatilidade (21 dias)', color='orange')
    ax2.set_title('Evolução do Risco da Carteira')
    ax2.legend()

    plt.tight_layout()
    plt.show()

# Gera visualizações
plot_efficient_frontier()
plot_portfolio_allocation()
plot_performance_evolution()

# Exibe resultados
returns, risk = portfolio_performance(mean_returns, cov_matrix, optimal_weights)

print(f"\nResultados da Otimização:")
print(f"Retorno Esperado Anual: {returns*100:.2f}%")
print(f"Risco (Volatilidade) Anual: {risk*100:.2f}%")
print(f"Índice de Sharpe: {returns/risk:.2f}")

# Exibe alocação por ativo
print("\nAlocação por Ativo:")
for ticker, weight in zip(tickers, optimal_weights):
    print(f"{ticker}: {weight*100:.2f}%")