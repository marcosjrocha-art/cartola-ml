import { useState } from "react";
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

type Resposta = {
  titulares: Jogador[];
  banco: Jogador[];
  reserva_luxo?: Luxo;
  capitao?: Capitao;
  resumo?: any;
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

export default function App() {
  const [cartoletas, setCartoletas] = useState(200);
  const [formacao, setFormacao] = useState("4-3-3");
  const [resp, setResp] = useState<Resposta | null>(null);
  const [loading, setLoading] = useState(false);

  const gerar = async () => {
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/api/gerar-time", {
        cartoletas,
        formacao,
      });
      setResp(res.data);
    } catch (e) {
      alert("Erro ao gerar time. Backend está rodando?");
    }
    setLoading(false);
  };

  const luxoId = resp?.reserva_luxo?.atleta_id;
  const capId = resp?.capitao?.atleta_id;

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

        {loading && <p className="text-sm">Gerando time...</p>}
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

      {resp?.reserva_luxo?.expected_gain !== undefined && resp?.reserva_luxo?.p_reserva_supera_titular !== undefined && (
        <p className="text-xs mt-4 text-gray-700">
          Regra do Luxo: ele só entra se o titular da MESMA posição fizer menos pontos.
          Seleção: maior ganho esperado (aprox. E[max(0, reserva - titular)]) usando std_5.
          Ganho esperado: {resp.reserva_luxo.expected_gain.toFixed(2)} |
          Prob(reserva &gt; titular): {(resp.reserva_luxo.p_reserva_supera_titular * 100).toFixed(1)}%
        </p>
      )}
    </div>
  );
}
