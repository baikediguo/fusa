import numpy as np
from kyupy import verilog, Timers, logic_sim
from kyupy.logic import unpackbits, packbits
from kyupy.techlib import SAED90
from tqdm import tqdm
import os


class FMAlogic(logic_sim.LogicSim):
    def __init__(self, netlist_path, sims=1024):
        print(f"\n📦 加载网表: {netlist_path}")
        circuit = verilog.load(netlist_path, tlib=SAED90)
        circuit.resolve_tlib_cells(SAED90)
        super().__init__(circuit, sims, m=2, c_reuse=False, strip_forks=False)

        self.circuit = circuit
        self.timers = Timers()

        self.a_locs = self._get_locs('activation_reg')
        self.b_locs = self._get_locs('weight_reg')
        self.s_locs = self._get_locs('i_sum')
        self.r_locs = self._get_locs('o_sum_reg')

        print("\n🔍 关键寄存器位置:")
        print(f"activation_reg: {self.a_locs}")
        print(f"weight_reg: {self.b_locs}")
        print(f"i_sum: {self.s_locs}")
        print(f"o_sum_reg: {self.r_locs}")

        self.candidate_nodes = self._get_candidate_nodes()
        print(f"\n✅ 候选故障点数量: {len(self.candidate_nodes)}")
        print(f"前5个候选故障点: {self.candidate_nodes[:5]}")

    def _get_locs(self, name):
        try:
            return self.circuit.s_locs(name)
        except:
            return []

    def _get_candidate_nodes(self):
        nodes = []
        for inst in self.circuit.instances:
            if inst.is_cell:
                for pin in inst.pins:
                    if pin.direction in ["output", "out"] and pin.net:
                        nodes.append(pin.net.index)
        return list(set(nodes))

    def sim(self, a, b, s, fault=None):
        shape = a.shape
        a, b, s = a.astype(np.int8), b.astype(np.int8), s.astype(np.int32)
        nbytes = int(np.ceil(len(a)/8))

        self.s[0, self.a_locs, 0, :nbytes] = np.packbits(unpackbits(a).T, axis=-1)
        self.s[0, self.b_locs, 0, :nbytes] = np.packbits(unpackbits(b).T, axis=-1)
        self.s[0, self.s_locs, 0, :nbytes] = np.packbits(unpackbits(s).T[:24], axis=-1)

        self.s_to_c()

        if fault:
            fault_node, fault_val = fault
            self.c[0, fault_node, 0, :] = 0xFF if fault_val == 1 else 0x00
            print(f"⚡ 注入故障: 节点 {fault_node} stuck-at-{fault_val}")

        self.c_prop()
        self.c_to_s()
        r_bits = np.unpackbits(self.s[1, self.r_locs, 0, :nbytes], axis=-1).T
        return packbits(r_bits, dtype=np.int32)[:len(a)].reshape(shape)


if __name__ == '__main__':
    print("="*55)
    print("🚀 启动门级故障注入评估框架")
    print("="*55)

    netlist_path = os.path.join(os.path.dirname(__file__), 'hw', 'pe.synth_dct.v.gz')
    fma = FMAlogic(netlist_path, sims=1024)

    # 生成输入向量
    rng = np.random.default_rng(42)
    a = rng.integers(-128, 127, fma.sims)
    b = rng.integers(-128, 127, fma.sims)
    s = rng.integers(-2**20, 2**20, fma.sims)

    # 运行无故障仿真
    golden = fma.sim(a, b, s)
    print(f"无故障输出样例: {golden[:5]}")

    # 故障注入评估
    results = []
    print("\n🚀 开始故障注入与RMSE评估...")
    for node in tqdm(fma.candidate_nodes[:10]):
        rmse_vals = []
        for stuck in [0, 1]:
            faulty_out = fma.sim(a, b, s, fault=(node, stuck))
            rmse = np.sqrt(np.mean((golden - faulty_out) ** 2))
            rmse_vals.append(rmse)
            print(f"📊 节点 {node} SA{stuck} RMSE={rmse:.4f}")
        results.append((node, *rmse_vals))

    # 选出关键故障点
    results.sort(key=lambda x: max(x[1], x[2]), reverse=True)
    print("\n📌 Top 10 RMSE Faults:")
    for node, r0, r1 in results[:10]:
        print(f"节点 {node}: SA0={r0:.4f}, SA1={r1:.4f}")

    FS = [node for node, r0, r1 in results if max(r0, r1) > 100.0]  # 可调阈值
    print("\n✅ 最终关键 Fault Set (FS):")
    print(FS)
