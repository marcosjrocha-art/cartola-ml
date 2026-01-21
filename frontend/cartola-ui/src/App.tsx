import { useMemo, useState } from "react";
import axios from "axios";

type Jogador = {
  atleta_id?: number;
  nome?: string;
  apelido?: string;
  slug?: string;
  clube_id?: number;
  clube_nome?: string;
  pos?: string;
  posicao_id?: number;
  preco: number;
  pred: number;
  std_5?: number;
};

type Luxo = {
  atleta_id?: number;
  nome?: string;
  pos?: string;
  clube_nome?: string;
  expected_gain?: number;
  p_reserva_supera_titular?: number;
};

type Capitao = {
  atleta_id?: number;
  nome?: string;
  pos?: string;
  pred?: number;
  clube_nome?: string;
};

type RespostaTime = {
  titulares: Jogador[];
  banco: Jogador[];
  reserva_luxo?: Luxo;
  capitao?: Capitao;
  resumo?: any;
};

type BacktestPoint = {
  season: number;
  rodada: number;
  pontos_reais: number;
  pontos_previstos: number;
  pontos_reais_baseline: number;
  topk_hit_rate: number;
  luxo_usou: boolean;
  luxo_delta: number;
  capitao: string;
  capitao_clube: string;
};

type BacktestResp = {
  config: any;
  metrics: any;
  series: BacktestPoint[];
};

function posLabel(j: Jogador) {
  if (j.pos) return j.pos;
  const map: Record<number, string> = { 1: "G", 2: "L", 3: "Z", 4: "M", 5: "A" };
  return j.posicao_id ? map[j.posicao_id] : "?";
}

function nomeLabel(j: Jogador) {
  return j.apelido || j.nome || "Sem nome";
}

function clubeLabel(j: Jogador) {
  return j.clube_nome || (j.clube_id !== undefined ? `Clube ${j.clube_id}` : "");
}

function LineChartSVG({ series }: { series: BacktestPoint[] }) {
  const w = 900;
  const h = 220;
  const pad = 30;

  if (!series.length) return null;

  const xs = series.map((_, i) => i);
  const allY = series.flatMap(s => [s.pontos_reais, s.pontos_previstos, s.pontos_reais_baseline]);

  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...allY);
  const yMax = Math.max(...allY);

  const xScale = (x: number) => {
    if (xMax === xMin) return pad;
    return pad + ((x - xMin) / (xMax - xMin)) * (w - pad * 2);
  };
  const yScale = (y: number) => {
    if (yMax === yMin) return h - pad;
    return (h - pad) - ((y - yMin) / (yMax - yMin)) * (h - pad * 2);
  };

  const pathFrom = (vals: number[]) =>
    vals.map((y, i) => `${i === 0 ? "M" : "L"} ${xScale(i).toFixed(2)} ${yScale(y).toFixed(2)}`).join(" ");

  const realPath = pathFrom(series.map(s => s.pontos_reais));
  const predPath = pathFrom(series.map(s => s.pontos_previstos));
  const basePath = pathFrom(series.map(s => s.pontos_reais_baseline));

  return (
    <div className="overflow-x-auto">
      <svg width={w} height={h} className="bg-white rounded shadow">
        {/* eixo */}
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="black" />
        <line x1={pad} y1={pad} x2={pad} y2={h - pad} stroke="black" />

        {/* linhas */}
        <path d={realPath} fill="none" stroke="black" strokeWidth={2} />
        <path d={predPath} fill="none" stroke="gray" strokeWidth={2} strokeDasharray="6 4" />
        <path d={basePath} fill="none" stroke="black" strokeWidth={1} strokeDasharray="2 6" />

        {/* legenda */}
        <text x={pad + 10} y={pad + 10} fontSize="12">Real (preto)</text>
        <text x={pad + 10} y={pad + 26} fontSize="12">Previsto (cinza tracejado)</text>
        <text x={pad + 10} y={pad + 42} fontSize="12">Baseline (pontilhado)</text>
      </svg>
    </div>
  );
}

export default function App() {
  const [cartoletas, setCartoletas] = useState(200);
  const [formacao, setFormacao] = useState("4-3-3");

  const [resp, setResp] = useState<RespostaTime | null>(null);
  const [loading, setLoading] = useState(false);

  const [bt, setBt] = useState<BacktestResp | null>(null);
  const [btLoading, setBtLoading] = useState(false);

  const gerar = async () => {
    setLoading(true);
    try {
      const res = await axios.post("import.meta.env.VITE_API_BASE/api/gerar-time", {
        cartoletas,
        formacao,
      });
      setResp(res.data);
    } catch (e) {
      alert("Erro ao gerar time. Backend está rodando?");
    }
    setLoading(false);
  };

  const carregarBacktest = async () => {
    setBtLoading(true);
    try {
      const res = await axios.get("import.meta.env.VITE_API_BASE/api/backtest/resumo", {
        params: { cartoletas, formacao, top_k: 20, min_train_rounds: 5 },
      });
      setBt(res.data);
    } catch (e) {
      alert("Erro ao carregar backtest. Veja o terminal do backend.");
    }
    setBtLoading(false);
  };

  const luxoId = resp?.reserva_luxo?.atleta_id;
  const capId = resp?.capitao?.atleta_id;

  const btPreview = useMemo(() => {
    if (!bt?.series?.length) return [];
    return bt.series.slice(-20); // mostra as últimas 20 rodadas avaliadas
  }, [bt]);

  return (
    <div className="min-h-screen bg-green-50 p-6">
      <h1 className="text-2xl font-bold mb-4">⚽ Cartola ML</h1>

      <div className="flex flex-wrap gap-4 mb-6 items-center">
        <input
          type="number"
          value={cartoletas}
          onChange={(e) => setCartoletas(Number(e.target.value))}
          className="border p-2 rounded w-40"
        />

        <select
          value={formacao}
          onChange={(e) => setFormacao(e.target.value)}
          className="border p-2 rounded"
        >
          <option>4-3-3</option>
          <option>4-4-2</option>
          <option>3-4-3</option>
          <option>3-5-2</option>
          <option>5-3-2</option>
        </select>

        <button onClick={gerar} className="bg-green-600 text-white px-4 py-2 rounded">
          Gerar Time
        </button>

        <button
          onClick={carregarBacktest}
          className="bg-black text-white px-4 py-2 rounded"
        >
          Carregar Backtest
        </button>

        {loading && <p className="text-sm">Gerando time...</p>}
        {btLoading && <p className="text-sm">Rodando backtest (pode levar um pouco)...</p>}
      </div>

      {resp?.resumo && (
        <div className="bg-white p-4 rounded shadow mb-6">
          <div className="flex flex-wrap gap-6 text-sm">
            <div><b>Custo titulares:</b> {resp.resumo.custo_titulares}</div>
            <div><b>Pontos (sem capitão):</b> {resp.resumo.pontos_previstos_titulares_sem_capitao}</div>
            <div><b>Bônus capitão (+50%):</b> {resp.resumo.bonus_capitao}</div>
            <div><b>Total com capitão:</b> {resp.resumo.pontos_previstos_total_com_capitao}</div>
            <div><b>Custo total:</b> {resp.resumo.custo_total}</div>

            {resp.capitao?.nome && (
              <div>
                <b>Capitão:</b> {resp.capitao.nome} ({resp.capitao.pos}) — {resp.capitao.clube_nome}
              </div>
            )}

            {resp.reserva_luxo?.nome && (
              <div>
                <b>Reserva de Luxo:</b> {resp.reserva_luxo.nome} ({resp.reserva_luxo.pos}) — {resp.reserva_luxo.clube_nome}
              </div>
            )}
          </div>
        </div>
      )}

      <h2 className="text-xl font-semibold mb-2">Titulares (11)</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {resp?.titulares?.map((j, i) => {
          const isCap = capId !== undefined && j.atleta_id === capId;
          return (
            <div key={i} className="bg-white p-4 rounded shadow relative">
              {isCap && (
                <span className="absolute top-2 right-2 text-xs bg-yellow-500 text-white px-2 py-1 rounded">
                  Capitão (x1.5)
                </span>
              )}
              <p className="font-bold">{nomeLabel(j)}</p>
              <p className="text-xs text-gray-600">
                {clubeLabel(j)} • ID {j.atleta_id ?? "-"}
              </p>
              <p className="text-sm">{posLabel(j)}</p>
              <p className="text-sm">💰 {Number(j.preco).toFixed(2)}</p>
              <p className="text-sm">⭐ {Number(j.pred).toFixed(2)}</p>
            </div>
          );
        })}
      </div>

      <h2 className="text-xl font-semibold mb-2">Banco (5) + Reserva de Luxo</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {resp?.banco?.map((j, i) => {
          const isLuxo = luxoId !== undefined && j.atleta_id === luxoId;
          return (
            <div key={i} className="bg-white p-4 rounded shadow relative">
              {isLuxo && (
                <span className="absolute top-2 right-2 text-xs bg-purple-600 text-white px-2 py-1 rounded">
                  Reserva de Luxo
                </span>
              )}
              <p className="font-bold">{nomeLabel(j)}</p>
              <p className="text-xs text-gray-600">
                {clubeLabel(j)} • ID {j.atleta_id ?? "-"}
              </p>
              <p className="text-sm">{posLabel(j)}</p>
              <p className="text-sm">💰 {Number(j.preco).toFixed(2)}</p>
              <p className="text-sm">⭐ {Number(j.pred).toFixed(2)}</p>
            </div>
          );
        })}
      </div>

      {bt?.metrics && (
        <div className="mt-10">
          <h2 className="text-xl font-semibold mb-2">Backtest</h2>

          <div className="bg-white p-4 rounded shadow mb-4 text-sm flex flex-wrap gap-6">
            <div><b>MAE (time):</b> {bt.metrics.mae_team}</div>
            <div><b>RMSE (time):</b> {bt.metrics.rmse_team}</div>
            <div><b>Correlação:</b> {bt.metrics.corr_team}</div>
            <div><b>Top-K hit rate:</b> {bt.metrics.topk_hit_rate_mean}</div>
            <div><b>Retorno médio vs baseline:</b> {bt.metrics.retorno_medio_vs_baseline}</div>
            <div><b>Rodadas avaliadas:</b> {bt.metrics.n_rodadas_avaliadas}</div>
          </div>

          <LineChartSVG series={btPreview} />

          <div className="mt-4 overflow-x-auto">
            <table className="min-w-[900px] bg-white rounded shadow text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">Temporada</th>
                  <th className="p-2 text-left">Rodada</th>
                  <th className="p-2 text-left">Real</th>
                  <th className="p-2 text-left">Previsto</th>
                  <th className="p-2 text-left">Real Baseline</th>
                  <th className="p-2 text-left">Top-K</th>
                  <th className="p-2 text-left">Luxo usou</th>
                  <th className="p-2 text-left">Δ Luxo</th>
                  <th className="p-2 text-left">Capitão</th>
                </tr>
              </thead>
              <tbody>
                {btPreview.map((r, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{r.season}</td>
                    <td className="p-2">{r.rodada}</td>
                    <td className="p-2">{r.pontos_reais}</td>
                    <td className="p-2">{r.pontos_previstos}</td>
                    <td className="p-2">{r.pontos_reais_baseline}</td>
                    <td className="p-2">{r.topk_hit_rate}</td>
                    <td className="p-2">{r.luxo_usou ? "sim" : "não"}</td>
                    <td className="p-2">{r.luxo_delta}</td>
                    <td className="p-2">{r.capitao}{r.capitao_clube ? ` (${r.capitao_clube})` : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-gray-600 mt-2">
              (Mostrando as últimas 20 rodadas avaliadas no backtest para manter leve.)
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
