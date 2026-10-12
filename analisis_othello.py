"""
analisis_othello.py
Análisis estadístico de los torneos de Othello y figuras del artículo.

Entradas (datos/): resultados_othello.csv, posiciones_othello.csv
Salidas  (datos/): estadisticas_othello.csv, elo_othello.csv, profundidad_othello.csv,
                   correlacion_othello.csv, pruebas_chi2_othello.csv
Figuras (articulo/figuras/): othello_profundidad.pdf, othello_loglog.pdf, othello_correlacion.pdf

Métodos: test binomial exacto (H0: p = 0.5, empates excluidos), IC de Wilson al 95 %,
bootstrap por pares de apertura (10 000 remuestreos) para la diferencia media de fichas,
chi-cuadrado, Elo por máxima verosimilitud (Bradley-Terry, empate = 0.5) y
correlación de Pearson/Spearman entre E(s) en posiciones intermedias y la diferencia final.
"""

import csv
import os
from collections import defaultdict
from math import sqrt, log10

import numpy as np
from scipy import stats, optimize

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from evaluador import EvaluadorOthello as EV
from AgentesEspecificos.AgenteOthello import AgenteOthello

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, '..', '..', 'datos')
FIGS = os.path.join(AQUI, '..', '..', 'articulo', 'figuras')
os.makedirs(FIGS, exist_ok=True)
plt.rcParams.update({'font.family': 'serif', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False})
AZUL, NARANJA, GRIS, VERDE = '#2a6f97', '#d17a22', '#7f7f7f', '#4c956c'


def wilson(k, n, z=1.959964):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - m, c + m


def leer(nombre):
    with open(os.path.join(DATOS, nombre), encoding='utf-8') as f:
        return list(csv.DictReader(f))


def escribir(nombre, filas):
    with open(os.path.join(DATOS, nombre), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def bootstrap_pares(difs_por_par, B=10_000, semilla=0):
    rng = np.random.default_rng(semilla)
    medias_par = np.array([np.mean(v) for v in difs_por_par])
    idx = rng.integers(0, len(medias_par), size=(B, len(medias_par)))
    return np.percentile(medias_par[idx].mean(axis=1), [2.5, 97.5])


def resumen_experimento(fs):
    a, b = fs[0]['agente_a'], fs[0]['agente_b']
    n = len(fs)
    va = sum(f['ganador'] == a for f in fs)
    vb = sum(f['ganador'] == b for f in fs)
    e = n - va - vb
    dif = np.array([int(f['diferencia_fichas']) for f in fs])
    pares = defaultdict(list)
    for f in fs:
        pares[f['semilla_apertura']].append(int(f['diferencia_fichas']))
    lo_b, hi_b = bootstrap_pares(list(pares.values()))
    nd = va + vb
    test = stats.binomtest(va, nd, 0.5) if nd else None
    wl, wh = wilson(va, nd)
    return {
        'experimento': fs[0]['experimento'], 'agente_a': a, 'agente_b': b, 'n': n,
        'victorias_a': va, 'victorias_b': vb, 'empates': e,
        'tasa_a': round(va / nd, 4) if nd else '', 'wilson_lo': round(wl, 4), 'wilson_hi': round(wh, 4),
        'p_binomial': float(f"{test.pvalue:.3g}") if test else '',
        'dif_media_a': round(dif.mean(), 2), 'dif_sd': round(dif.std(ddof=1), 2),
        'boot_lo': round(lo_b, 2), 'boot_hi': round(hi_b, 2),
        'tiempo_a_ms': round(1000 * np.mean([float(f['tiempo_a']) for f in fs]), 2),
        'tiempo_b_ms': round(1000 * np.mean([float(f['tiempo_b']) for f in fs]), 2),
        'nodos_a': round(np.mean([float(f['nodos_a']) for f in fs]), 1),
        'nodos_b': round(np.mean([float(f['nodos_b']) for f in fs]), 1),
        'nodos_seg_a': round(np.mean([float(f['nodos_seg_a']) for f in fs]), 0),
        'nodos_seg_b': round(np.mean([float(f['nodos_seg_b']) for f in fs]), 0),
        'evals_a': round(np.mean([float(f['evals_a']) for f in fs]), 1),
        'evals_b': round(np.mean([float(f['evals_b']) for f in fs]), 1),
        'prof_max_a': max(int(f['prof_max_a']) for f in fs),
        'prof_max_b': max(int(f['prof_max_b']) for f in fs),
    }


def elo(rr):
    """Bradley-Terry por máxima verosimilitud; empate cuenta 0.5. Media fijada en 1500."""
    agentes = sorted({f['agente_a'] for f in rr} | {f['agente_b'] for f in rr})
    idx = {a: i for i, a in enumerate(agentes)}
    juegos = []
    for f in rr:
        s = 1.0 if f['ganador'] == f['agente_a'] else 0.0 if f['ganador'] == f['agente_b'] else 0.5
        juegos.append((idx[f['agente_a']], idx[f['agente_b']], s))

    def nll(r):
        r = np.concatenate([[0.0], r])
        out = 0.0
        for i, j, s in juegos:
            p = 1 / (1 + 10 ** ((r[j] - r[i]) / 400))
            p = min(max(p, 1e-9), 1 - 1e-9)
            out -= s * np.log(p) + (1 - s) * np.log(1 - p)
        return out
    res = optimize.minimize(nll, np.zeros(len(agentes) - 1), method='BFGS')
    r = np.concatenate([[0.0], res.x])
    r = r - r.mean() + 1500
    puntos = defaultdict(float)
    partidas = defaultdict(int)
    for i, j, s in juegos:
        puntos[i] += s
        puntos[j] += 1 - s
        partidas[i] += 1
        partidas[j] += 1
    return [{'agente': a, 'elo': round(r[idx[a]], 1), 'puntos': puntos[idx[a]], 'partidas': partidas[idx[a]]}
            for a in agentes]


def totales_agente(rr):
    t = defaultdict(lambda: {'V': 0, 'D': 0, 'E': 0, 'dif': []})
    for f in rr:
        a, b, g = f['agente_a'], f['agente_b'], f['ganador']
        d = int(f['diferencia_fichas'])
        for ag, signo in ((a, 1), (b, -1)):
            if g == 'Empate':
                t[ag]['E'] += 1
            elif g == ag:
                t[ag]['V'] += 1
            else:
                t[ag]['D'] += 1
            t[ag]['dif'].append(signo * d)
    return t


def evaluar_negro(tablero, func, agente):
    m1 = len(agente._get_valid_moves(tablero, 1))
    m2 = len(agente._get_valid_moves(tablero, 2))
    return func(tablero, 1, 2, m1, m2), m1, m2


def correlaciones():
    pos = leer('posiciones_othello.csv')
    ag = AgenteOthello()
    por_corte = defaultdict(lambda: defaultdict(list))
    for f in pos:
        t = np.array([int(c) for c in f['tablero']], dtype=int).reshape(8, 8)
        c = int(f['corte'])
        e1, m1, m2 = evaluar_negro(t, EV.evaluar_estatica, ag)
        d = por_corte[c]
        d['E1'].append(e1)
        d['E2'].append(EV.evaluar_adaptativa(t, 1, 2, m1, m2))
        d['E3'].append(EV.evaluar_adaptativa_dinamica(t, 1, 2, m1, m2))
        d['f_P'].append(EV.paridad_fichas(t, 1, 2)[0])
        d['f_M'].append(EV.movilidad_relativa(m1, m2))
        d['f_C'].append(EV.control_esquinas(t, 1, 2))
        d['f_T'].append(EV.valor_posicional(t, 1, 2))
        d['final'].append(int(f['dif_final_negro']))
    filas = []
    for c in sorted(por_corte):
        d = por_corte[c]
        fin = np.array(d['final'])
        for k in ['E1', 'E2', 'E3', 'f_P', 'f_M', 'f_C', 'f_T']:
            x = np.array(d[k])
            pr = stats.pearsonr(x, fin)
            sp = stats.spearmanr(x, fin)
            filas.append({'fichas': c, 'variable': k, 'n': len(fin),
                          'pearson': round(pr[0], 4), 'p_pearson': float(f"{pr[1]:.3g}"),
                          'spearman': round(sp[0], 4), 'p_spearman': float(f"{sp[1]:.3g}")})
    escribir('correlacion_othello.csv', filas)
    return filas


def main():
    filas = leer('resultados_othello.csv')
    grupos = defaultdict(list)
    for f in filas:
        grupos[f['experimento']].append(f)
    resumen = [resumen_experimento(fs) for fs in grupos.values()]
    escribir('estadisticas_othello.csv', resumen)
    for r in resumen:
        print(r)

    rr = [f for f in filas if f['experimento'].startswith('rr_')]
    elos = elo(rr)
    tot = totales_agente(rr)
    for e in elos:
        t = tot[e['agente']]
        e.update({'victorias': t['V'], 'derrotas': t['D'], 'empates': t['E'],
                  'dif_media': round(np.mean(t['dif']), 2)})
    escribir('elo_othello.csv', elos)
    print(elos)

    # chi-cuadrado
    pruebas = []
    tabla = [[r['victorias_a'], r['victorias_b']] for r in resumen if r['experimento'].startswith('rr_')]
    if len(tabla) >= 2:
        chi2, p, gl, _ = stats.chi2_contingency(tabla)
        pruebas.append({'prueba': 'homogeneidad_round_robin (victorias A/B por cruce)', 'chi2': round(chi2, 3),
                        'gl': gl, 'p': float(f"{p:.3g}")})
    for r in resumen:
        o = [r['victorias_a'], r['victorias_b']]
        if sum(o):
            c, p = stats.chisquare(o)
            pruebas.append({'prueba': f"50_50_{r['experimento']}", 'chi2': round(c, 3), 'gl': 1,
                            'p': float(f"{p:.3g}")})
    # ventaja de color: victorias de negras vs blancas (partidas decididas), por grupo de experimentos
    def color(fs):
        vn = vb = 0
        for f in fs:
            if f['ganador'] == 'Empate':
                continue
            if (f['ganador'] == f['agente_a']) == (f['color_a'] == 'negro'):
                vn += 1
            else:
                vb += 1
        return vn, vb
    grupos_color = {
        'espejo (E1,E2,E3 vs si mismos)': [f for f in filas if f['experimento'].startswith('espejo_')],
        'round_robin': [f for f in filas if f['experimento'].startswith('rr_')],
        'todas': filas,
    }
    for k in grupos_color:
        for exp in sorted({f['experimento'] for f in grupos_color[k]}) if k == 'espejo (E1,E2,E3 vs si mismos)' else []:
            vn, vb = color(grupos[exp])
            c, p = stats.chisquare([vn, vb])
            pruebas.append({'prueba': f'color_{exp}_negras_{vn}_blancas_{vb}', 'chi2': round(c, 3), 'gl': 1,
                            'p': float(f"{p:.3g}")})
        vn, vb = color(grupos_color[k])
        c, p = stats.chisquare([vn, vb])
        pruebas.append({'prueba': f'color_{k}_negras_{vn}_blancas_{vb}', 'chi2': round(c, 3), 'gl': 1,
                        'p': float(f"{p:.3g}")})
    escribir('pruebas_chi2_othello.csv', pruebas)
    print(pruebas)

    # curva de profundidad
    prof = []
    for r in resumen:
        if not r['experimento'].startswith('prof_'):
            continue
        fs = grupos[r['experimento']]
        d = int(fs[0]['profundidad_a'])
        tiempos = [float(f['tiempo_a']) for f in fs]
        prof.append({'profundidad': d, 'n': r['n'], 'victorias': r['victorias_a'],
                     'derrotas': r['victorias_b'], 'empates': r['empates'],
                     'tasa': r['tasa_a'], 'wilson_lo': r['wilson_lo'], 'wilson_hi': r['wilson_hi'],
                     'p_binomial': r['p_binomial'], 'dif_media': r['dif_media_a'],
                     'tiempo_ms': round(1000 * np.mean(tiempos), 2),
                     'tiempo_ms_sd': round(1000 * np.std(tiempos, ddof=1), 2),
                     'nodos': r['nodos_a'], 'nodos_seg': r['nodos_seg_a'], 'evals': r['evals_a']})
    # d = 4: el rival es idéntico (E1, d = 4); la tasa es 0.5 por simetría y no se juega.
    # Tiempo y nodos de d = 4 se toman de las partidas espejo E1 vs E1 (ambos lados d = 4).
    if 'espejo_E1' in grupos and prof:
        fs = grupos['espejo_E1']
        t4 = [float(f['tiempo_a']) for f in fs] + [float(f['tiempo_b']) for f in fs]
        n4 = [float(f['nodos_a']) for f in fs] + [float(f['nodos_b']) for f in fs]
        s4 = [float(f['nodos_seg_a']) for f in fs] + [float(f['nodos_seg_b']) for f in fs]
        e4 = [float(f['evals_a']) for f in fs] + [float(f['evals_b']) for f in fs]
        prof.append({'profundidad': 4, 'n': '', 'victorias': '', 'derrotas': '', 'empates': '',
                     'tasa': 0.5, 'wilson_lo': '', 'wilson_hi': '', 'p_binomial': '', 'dif_media': 0,
                     'tiempo_ms': round(1000 * np.mean(t4), 2), 'tiempo_ms_sd': round(1000 * np.std(t4, ddof=1), 2),
                     'nodos': round(np.mean(n4), 1), 'nodos_seg': round(np.mean(s4), 0), 'evals': round(np.mean(e4), 1)})
    prof.sort(key=lambda x: x['profundidad'])
    if prof:
        ds = np.array([p['profundidad'] for p in prof], float)
        ts = np.array([p['tiempo_ms'] for p in prof], float)
        ns = np.array([p['nodos'] for p in prof], float)
        for p_, i in zip(prof, range(len(prof))):
            p_['factor_ramif_efectivo'] = round(ns[i] / ns[i - 1], 3) if i else ''
        escribir('profundidad_othello.csv', prof)
        # ajustes: exponencial (log t vs d) y potencia (log t vs log d)
        exp_fit = stats.linregress(ds, np.log10(ts))
        pot_fit = stats.linregress(np.log10(ds), np.log10(ts))
        lin_nodos = stats.linregress(ns, ts)
        ajustes = [{'modelo': 'exponencial log10(t)=a+b*d', 'pendiente': round(exp_fit.slope, 4),
                    'intercepto': round(exp_fit.intercept, 4), 'r2': round(exp_fit.rvalue ** 2, 4),
                    'factor_por_nivel': round(10 ** exp_fit.slope, 3)},
                   {'modelo': 'potencia log10(t)=a+k*log10(d)', 'pendiente': round(pot_fit.slope, 4),
                    'intercepto': round(pot_fit.intercept, 4), 'r2': round(pot_fit.rvalue ** 2, 4),
                    'factor_por_nivel': ''},
                   {'modelo': 'lineal t=a+b*nodos (ms por nodo)', 'pendiente': round(lin_nodos.slope, 5),
                    'intercepto': round(lin_nodos.intercept, 3), 'r2': round(lin_nodos.rvalue ** 2, 4),
                    'factor_por_nivel': ''}]
        escribir('ajustes_profundidad_othello.csv', ajustes)
        print(prof, ajustes)
        fig_profundidad(prof)
        fig_loglog(prof, exp_fit, pot_fit)

    fig_correlacion(correlaciones())


def fig_profundidad(prof):
    d = [p['profundidad'] for p in prof]
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.5))
    jug = [p for p in prof if p['wilson_lo'] != '']
    dj = [p['profundidad'] for p in jug]
    t = np.array([p['tasa'] for p in jug], float)
    lo = t - np.array([p['wilson_lo'] for p in jug])
    hi = np.array([p['wilson_hi'] for p in jug]) - t
    axs[0].errorbar(dj, t, yerr=[lo, hi], fmt='o-', color=AZUL, capsize=3, label='medido (100 partidas)')
    if 4 in d and 4 not in dj:
        axs[0].plot([4], [0.5], 'o', mfc='white', mec=AZUL, label='d = 4: 0.5 por simetría')
        axs[0].plot([4, dj[0]], [0.5, t[0]], ':', color=AZUL)
    axs[0].legend(frameon=False, fontsize=7, loc='lower right')
    axs[0].axhline(0.5, color=GRIS, ls='--', lw=1)
    axs[0].set_xticks(d)
    axs[0].set_ylim(0, 1)
    axs[0].set_xlabel('Profundidad de E1 (rival: E1, d = 4)')
    axs[0].set_ylabel('Tasa de victorias (IC Wilson 95 %)')
    axs[1].plot(d, [p['tiempo_ms'] for p in prof], 'o-', color=NARANJA, label='tiempo por jugada (ms)')
    axs[1].plot(d, [p['nodos'] for p in prof], 's--', color=VERDE, label='nodos por jugada')
    axs[1].set_yscale('log')
    axs[1].set_xticks(d)
    axs[1].set_xlabel('Profundidad')
    axs[1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, 'othello_profundidad.pdf'))
    plt.close(fig)


def fig_loglog(prof, exp_fit, pot_fit):
    d = np.array([p['profundidad'] for p in prof], float)
    t = np.array([p['tiempo_ms'] for p in prof], float)
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    ax.loglog(d, t, 'o', color=NARANJA, label='medido')
    dd = np.linspace(d.min(), d.max(), 50)
    ax.loglog(dd, 10 ** (pot_fit.intercept + pot_fit.slope * np.log10(dd)), '--', color=GRIS,
              label=f'potencia $t\\propto d^{{{pot_fit.slope:.1f}}}$ ($R^2$={pot_fit.rvalue ** 2:.3f})')
    ax.loglog(dd, 10 ** (exp_fit.intercept + exp_fit.slope * dd), '-', color=AZUL,
              label=f'exponencial $t\\propto {10 ** exp_fit.slope:.2f}^d$ ($R^2$={exp_fit.rvalue ** 2:.3f})')
    ax.set_xticks(d)
    ax.set_xticklabels([str(int(x)) for x in d])
    ax.minorticks_off()
    ax.set_xlabel('Profundidad $d$ (escala log)')
    ax.set_ylabel('Tiempo por jugada (ms, log)')
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, 'othello_loglog.pdf'))
    plt.close(fig)


def fig_correlacion(filas):
    cortes = sorted({f['fichas'] for f in filas})
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    estilos = {'E1': ('o-', AZUL), 'E2': ('s-', NARANJA), 'E3': ('^-', VERDE),
               'f_M': ('x--', GRIS), 'f_P': ('d:', '#9b5de5')}
    etiquetas = {'E1': '$E_1$', 'E2': '$E_2$', 'E3': '$E_3$', 'f_M': '$f_M$ (movilidad)',
                 'f_P': '$f_P$ (paridad)'}
    for k, (m, c) in estilos.items():
        y = [next(f['spearman'] for f in filas if f['fichas'] == x and f['variable'] == k) for x in cortes]
        ax.plot(cortes, y, m, color=c, label=etiquetas[k])
    ax.axhline(0, color=GRIS, lw=0.6)
    ax.set_xticks(cortes)
    ax.set_xlabel('Fichas en el tablero')
    ax.set_ylabel(r'$\rho$ de Spearman con la dif. final')
    ax.legend(frameon=False, fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, 'othello_correlacion.pdf'))
    plt.close(fig)


if __name__ == '__main__':
    main()
