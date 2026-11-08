"""Genera web/index-en.html a partir de web/index.html (la pagina en espanol es la fuente).
Uso: python web/traducir_en.py     Sale con error si queda texto en espanol sin traducir."""
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
h = (W / "index.html").read_text(encoding="utf-8")

V = lambda s: f"<var>{s}</var>"
FRAC = lambda n, d: f'<span class="frac"><span>{n}</span><span>{d}</span></span>'
paso = lambda etq, ec, txt: f'<li><span class="etq">{etq}</span><span class="ec">{ec}</span><p>{txt}</p></li>'
S0, Se, k = f"{V('S')}<sub>0</sub>", f"{V('S')}<sub>e</sub>", V("k")

# --- la seccion del modelo se rehace completa (tiene mucha notacion en linea) ---
MODELO = f'''<section id="modelo" class="seccion oscura">
  <div class="envoltura">
    <p class="antetitulo">2 · The model</p>
    <h2>From the continuity equation to a single exponential</h2>
    <p class="intro">The paper starts from the general sulfur balance in the ladle and, with two physical assumptions, reduces it to an ordinary differential equation with a closed-form solution.</p>
    <div class="resultado-modelo"><span class="etq">Result · eq. 6</span><span class="ec">{V('S')}({V('t')}) = {Se} + ({S0} − {Se}) e<sup>−{V('k t')}</sup></span><p>Sulfur decays exponentially from the initial value {S0} toward the equilibrium value {Se}; the whole problem comes down to knowing the rate constant {k}.</p></div>
    <details class="plegable">
      <summary>Show the step-by-step derivation (eqs. 1 to 6)</summary>
      <ol class="pasos">
        {paso("Sulfur balance · eq. 1", f"∂{V('S')}/∂{V('t')} + <b>v</b>·∇{V('S')} = {V('D')}<sub>S</sub> ∇²{V('S')} + {V('r')}<sub>S</sub>", f"Continuity equation: sulfur accumulates, travels with the flow (convection), diffuses and disappears by reaction at rate {V('r')}<sub>S</sub>. The paper writes it in cylindrical coordinates; here it is in compact form.")}
        {paso("Axial transport · eq. 2", f"∂{V('S')}/∂{V('t')} + {V('v')}<sub>z</sub> ∂{V('S')}/∂{V('z')} = {V('D')}<sub>S</sub> ∂²{V('S')}/∂{V('z')}² + {V('r')}<sub>S</sub>", f"Bubbles move mostly upward, so only the vertical direction {V('z')} is kept.")}
        {paso("Well-stirred tank · eq. 3", f"d{V('S')}/d{V('t')} = {V('r')}<sub>S</sub>", "Diffusion is small compared with convection and gas stirring leaves small concentration gradients: sulfur only changes with time.")}
        {paso("First-order kinetics · eqs. 4 and 5", f"{V('r')}<sub>S</sub> = −{k} ({V('S')} − {Se}) &nbsp;&nbsp; {k} = {V('k')}<sub>0</sub> e<sup>−{V('E')}<sub>a</sub>/{V('RT')}</sup>", f"The desulfurization rate is proportional to the distance from equilibrium {Se}. The constant {k} depends on temperature through Arrhenius; the model is isothermal, so {k} is fixed during injection.")}
        {paso("Solution · eq. 6", f"{V('S')}({V('t')}) = {Se} + ({S0} − {Se}) e<sup>−{V('k t')}</sup>", f"Sulfur decays exponentially from {S0} toward {Se}. Everything comes down to knowing {k}.")}
      </ol>
    </details>

    <h3 class="subtitulo-seccion">Where does {k} come from?</h3>
    <p class="intro">For lime, {k} is computed from the physics of injection, in three chained steps.</p>
    <ol class="pasos">
      {paso("Bubble rise · eq. 9", f"{V('v')}<sub>b</sub> = " + FRAC(f"{V('g')} ({V('ρ')}<sub>M</sub> − {V('ρ')}<sub>g</sub>) {V('d')}<sub>b</sub><sup>2</sup>", f"18 {V('μ')}<sub>M</sub>"), "Stokes' law: the bubble rises faster the larger the density difference and its diameter, and slower the more viscous the metal.")}
      {paso("Residence time · eq. 8", f"{V('t')}<sub>R</sub> = " + FRAC(f"{V('h')}<sub>i</sub>", f"{V('v')}<sub>b</sub>"), "The particle rides with the bubble from the lance tip to the surface. A deeper lance gives it more contact time with the metal.")}
      {paso("Lime rate constant · eq. 7, after Oeters", f"{V('k')}<sub>CaO</sub> = " + FRAC(f"6 {V('β')} {V('t')}<sub>R</sub> {V('q')}<sub>CaO</sub> {V('ρ')}<sub>M</sub>", f"{V('d')}<sub>p</sub> {V('w')}<sub>M</sub> {V('ρ')}<sub>CaO</sub>"), f"It grows with the mass transfer coefficient {V('β')}, the residence time and the lime feed rate. The term 6/{V('d')}<sub>p</sub> is the area per unit volume of a sphere: finer particles offer more surface and react faster. A ladle with more metal dilutes the effect.")}
    </ol>

    <h3 class="subtitulo-seccion">Mixtures and half-life</h3>
    <ol class="pasos">
      {paso("Co-injection · eq. 15", f"{V('k')}<sub>m</sub> = Σ {V('x')}<sub>i</sub> {V('k')}<sub>i</sub>", f"The rate constant of a mixture is the average of those of each powder, weighted by its mole fraction {V('x')}<sub>i</sub>. The compositions in table 3 are in weight percent and are converted to mole fractions with each powder's molar mass.")}
      {paso("Half-life · eq. 16", f"{V('t')}<sub>h</sub> = " + FRAC("ln 2", k), f"Time for the sulfur still to be removed, {V('S')} − {Se}, to halve. It does not depend on the initial sulfur, so it is a fair way to compare reagents.")}
    </ol>

    <div class="dos-columnas datos-modelo">
      <div>
        <h3>Parameters of the validation case</h3>
        <table class="tabla simbolos">
          <thead><tr><th>Symbol</th><th>Meaning</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>{V('β')}</td><td>mass transfer coefficient</td><td>6.3×10⁻⁵ m/s</td></tr>
            <tr><td>{V('q')}<sub>CaO</sub></td><td>lime feed rate</td><td>1.25 kg/s</td></tr>
            <tr><td>{V('ρ')}<sub>M</sub></td><td>hot metal density</td><td>7100 kg/m³</td></tr>
            <tr><td>{V('μ')}<sub>M</sub></td><td>hot metal viscosity</td><td>0.0067 kg/(m·s)</td></tr>
            <tr><td>{V('w')}<sub>M</sub></td><td>hot metal mass</td><td>150&#8239;000 kg</td></tr>
            <tr><td>{V('d')}<sub>p</sub></td><td>lime particle diameter</td><td>1.0×10⁻⁵ m</td></tr>
            <tr><td>{V('ρ')}<sub>CaO</sub></td><td>lime density</td><td>3345 kg/m³</td></tr>
            <tr><td>{V('h')}<sub>i</sub></td><td>lance immersion depth</td><td>2.0 m</td></tr>
            <tr><td>{V('d')}<sub>b</sub></td><td>bubble diameter</td><td>1.1725×10⁻³ m</td></tr>
            <tr><td>{V('ρ')}<sub>g</sub></td><td>gas density</td><td>1.165 kg/m³</td></tr>
            <tr><td>{Se}</td><td>equilibrium sulfur</td><td>0 wt %</td></tr>
          </tbody>
        </table>
        <p class="nota">Table 1 of the paper.</p>
      </div>
      <div>
        <h3>Validation</h3>
        <p class="parrafo">The validation case is lime desulfurization of 150 t of hot metal reported by Oeters (1989), with 0.1 % initial sulfur and 2400 s of injection. Table 1 gives {V('v')}<sub>b</sub> = 0.7938 m/s, {V('t')}<sub>R</sub> = 2.52 s and {k} = 0.001684 1/s, and the computed curve matches the reference data (figure 2 of the paper). Reproduced here, all three values agree to the fourth digit.</p>
        <h3>Co-injection mixtures</h3>
        <table class="tabla">
          <thead><tr><th>Mix</th><th>CaO</th><th>CaC₂</th><th>Mg</th><th>{V('k')}<sub>m</sub> (1/s)</th></tr></thead>
          <tbody>
            <tr><td>M1</td><td>0 %</td><td>50 %</td><td>50 %</td><td>0.002869</td></tr>
            <tr><td>M2</td><td>25 %</td><td>37.5 %</td><td>37.5 %</td><td>0.002664</td></tr>
            <tr><td>M3</td><td>50 %</td><td>25 %</td><td>25 %</td><td>0.002412</td></tr>
            <tr><td>M4</td><td>75 %</td><td>12.5 %</td><td>12.5 %</td><td>0.002095</td></tr>
            <tr><td>M5</td><td>100 %</td><td>0 %</td><td>0 %</td><td>0.001684</td></tr>
          </tbody>
        </table>
        <p class="nota">Table 3 of the paper, composition in weight percent. Rate constant of each powder (table 2): lime 0.001684 1/s (this model), CaC₂ 0.004 1/s (Zhao, 1992) and Mg 0.00244 1/s (Irons and Guthrie, 1981).</p>
      </div>
    </div>
  </div>
</section>

'''
a = h.index('<section id="modelo"'); b = h.index('<section id="gemelo"')
h = h[:a] + MODELO + h[b:]

PARES = [
    ('<html lang="es">', '<html lang="en">'),
    ("<title>Desulfuración de arrabio · gemelo digital</title>", "<title>Hot metal desulfurization · digital twin</title>"),
    ('content="Gemelo digital interactivo del modelo de desulfuración de arrabio por inyección de polvos de Barrón, Hilerio y Medina (2015), con simulación CFD 3D en OpenFOAM."',
     'content="Interactive digital twin of the hot metal desulfurization by powder injection model of Barrón, Hilerio and Medina (2015), with a 3D CFD simulation in OpenFOAM."'),
    ('Desulfuración <span>· gemelo digital</span>', 'Desulfurization <span>· digital twin</span>'),
    ('>Proceso</a>', '>Process</a>'), ('>Modelo</a>', '>Model</a>'), ('>Gemelo</a>', '>Twin</a>'), ('>Figuras</a>', '>Figures</a>'),
    ('>Método</a>', '>Method</a>'), ('>Créditos</a>', '>Credits</a>'),
    ('<p class="antetitulo">Gemelo digital interactivo</p>', '<p class="antetitulo">Interactive digital twin</p>'),
    ("Desulfuración de arrabio por inyección de polvos: el modelo cinético de Barrón, Hilerio y Medina (2015), llevado a un gemelo que se puede mover, y acompañado de una simulación de fluidos en 3D de la olla.",
     "Hot metal desulfurization by powder injection: the kinetic model of Barrón, Hilerio and Medina (2015), turned into a twin you can operate, together with a 3D fluid simulation of the ladle."),
    ("<dt>Olla</dt><dd>150 t <small>de arrabio</small></dd>", "<dt>Ladle</dt><dd>150 t <small>of hot metal</small></dd>"),
    ("<dt>Azufre con cal</dt>", "<dt>Sulfur with lime</dt>"), ("<small>en 40 min</small>", "<small>in 40 min</small>"),
    ("<small>celdas</small>", "<small>cells</small>"), ("<dt>Corridas</dt><dd>12 <small>casos en OpenFOAM</small>", "<dt>Runs</dt><dd>12 <small>OpenFOAM cases</small>"),
    ("Corte vertical de la olla por la lanza y las dos toberas. El color es la rapidez del arrabio y las líneas siguen su recorrido; ambos salen de la simulación CFD en OpenFOAM, no de una animación aproximada. Render en Blender.",
     "Vertical cut of the ladle through the lance and both nozzles. Color is the hot metal speed and the lines follow its path; both come from the OpenFOAM CFD simulation, not from an approximate animation. Rendered in Blender."),
    ("1 · El proceso", "1 · The process"), ("Quitar el azufre del arrabio antes de hacer acero", "Removing sulfur from hot metal before making steel"),
    ("El azufre vuelve frágil al acero: le quita ductilidad y tenacidad al impacto. Para fabricar aceros de bajo azufre, el arrabio que sale del alto horno se trata en la olla antes de pasar al convertidor de oxígeno.",
     "Sulfur makes steel brittle: it reduces ductility and impact toughness. To produce low-sulfur steels, the hot metal coming from the blast furnace is treated in the ladle before going to the oxygen converter."),
    ("En la inyección de polvos, una lanza refractaria sumergida en el baño sopla un gas inerte (argón o nitrógeno) que arrastra el reactivo en polvo. Las partículas suben junto con las burbujas, reaccionan con el azufre disuelto y el sulfuro que se forma flota hasta la escoria, donde queda atrapado.",
     "In powder injection, a refractory lance immersed in the bath blows an inert gas (argon or nitrogen) carrying the powdered reagent. The particles rise with the bubbles, react with the dissolved sulfur, and the sulfide formed floats up to the slag, where it is trapped."),
    ("Se usan tres reactivos, solos o mezclados. La cal es el más barato; el carburo de calcio y el magnesio desulfuran más rápido, pero cuestan más. El artículo estudia cada uno por separado (mono-inyección) y en mezclas (co-inyección).",
     "Three reagents are used, alone or mixed. Lime is the cheapest; calcium carbide and magnesium desulfurize faster but cost more. The paper studies each one alone (mono-injection) and in mixtures (co-injection)."),
    ('<span class="etq">Reacciones de desulfuración</span>', '<span class="etq">Desulfurization reactions</span>'),
    ("<small>cal</small>", "<small>lime</small>"), ("<small>carburo de calcio</small>", "<small>calcium carbide</small>"), ("<small>magnesio</small>", "<small>magnesium</small>"),
    ("[S] es el azufre disuelto en el arrabio. El producto sólido sube a la escoria.", "[S] is the sulfur dissolved in the hot metal. The solid product rises to the slag."),
    ('src="figura/olla.html" title="Estación de desulfuración seccionada, interactiva"', 'src="figura/olla-en.html" title="Cutaway desulfurization station, interactive"'),
    ("3 · Gemelo interactivo", "3 · Interactive twin"), ("Mueve la operación y mira cómo cambia la desulfuración", "Change the operation and watch desulfurization respond"),
    ("Las ecuaciones del artículo corren en vivo en el navegador. La curva naranja es la condición que eliges; la punteada, la misma mezcla con los valores del artículo.",
     "The paper's equations run live in your browser. The orange curve is the condition you choose; the dashed one, the same mix with the paper's values."),
    ("<legend>Mezcla de polvo</legend>", "<legend>Powder mix</legend>"), ("<legend>Operación</legend>", "<legend>Operation</legend>"),
    ("Volver a los valores del artículo", "Back to the paper's values"),
    ("<span>Constante de la mezcla</span>", "<span>Mix rate constant</span>"), ("<span>Vida media</span>", "<span>Half-life</span>"),
    ("<span>Azufre al final</span>", "<span>Final sulfur</span>"), ("<small>% en peso</small>", "<small>wt %</small>"),
    ("<span>Tiempo para 0.005 % S</span>", "<span>Time to 0.005 % S</span>"),
    ("<h3>Concentración de azufre contra tiempo</h3>", "<h3>Sulfur concentration versus time</h3>"), ("> escala logarítmica</label>", "> log scale</label>"),
    ("La cadena del modelo, en vivo", "The model chain, live"),
    ("<li><span>Burbuja</span>", "<li><span>Bubble</span>"), ("<li><span>Residencia</span>", "<li><span>Residence</span>"),
    ("<li><span>Cinética de la cal</span>", "<li><span>Lime kinetics</span>"), ("<li><span>Mezcla</span>", "<li><span>Mix</span>"),
    ("Las constantes del CaC₂ (0.004 1/s, Zhao 1992) y del Mg (0.00244 1/s, Irons y Guthrie 1981) son las de la tabla 2 del artículo y no dependen de los controles de operación; la de la cal sí, a través de la ec. 7.",
     "The CaC₂ (0.004 1/s, Zhao 1992) and Mg (0.00244 1/s, Irons and Guthrie 1981) constants come from table 2 of the paper and do not depend on the operating controls; the lime constant does, through eq. 7."),
    ("4 · Figuras del artículo", "4 · The paper's figures"), ("Las tres figuras de resultados, recalculadas", "The three results figures, recomputed"),
    ("Generadas con el mismo modelo que mueve al gemelo y con los parámetros de las tablas 1 a 3; los textos resumen la lectura que hace el artículo. Pasa el cursor sobre cada gráfica para leer los valores.",
     "Generated with the same model that drives the twin and the parameters of tables 1 to 3; the captions summarize the paper's reading. Hover over each chart to read the values."),
    ("<b>Figura 5.</b> Mono-inyección con 0.1 % de azufre inicial. El carburo de calcio es el más rápido, seguido del magnesio; la cal es la más lenta, sobre todo en la primera mitad de la inyección. El costo limita el uso de los dos primeros.",
     "<b>Figure 5.</b> Mono-injection with 0.1 % initial sulfur. Calcium carbide is the fastest, followed by magnesium; lime is the slowest, especially in the first half of injection. Cost limits the use of the first two."),
    ("<b>Figura 6.</b> Co-inyección de las cinco mezclas de la tabla 3. La mezcla sin cal desulfura más rápido; cada aumento de cal reduce <var>k</var><sub>m</sub> y hace más lenta la caída del azufre.",
     "<b>Figure 6.</b> Co-injection of the five mixtures in table 3. The lime-free mix desulfurizes fastest; each increase in lime lowers <var>k</var><sub>m</sub> and slows the sulfur decay."),
    ("<b>Figura 7.</b> Vida media contra el contenido de cal: sube de unos 242 s sin cal a 412 s con cal pura. Más cal hace más lenta la desulfuración, aunque la cal es el reactivo más barato.",
     "<b>Figure 7.</b> Half-life versus lime content: it rises from about 242 s without lime to 412 s with pure lime. More lime slows desulfurization, even though lime is the cheapest reagent."),
    ("<h3>Conclusiones del artículo</h3>", "<h3>The paper's conclusions</h3>"),
    ("Las burbujas del gas de arrastre agitan el baño; la simulación CFD respalda el supuesto de tanque bien agitado.", "Carrier gas bubbles stir the bath; the CFD simulation supports the well-stirred tank assumption."),
    ("El modelo de mono-inyección con cal, validado con datos de la literatura, representa el proceso de forma cuantitativa.", "The lime mono-injection model, validated against literature data, represents the process quantitatively."),
    ("Se propone una constante de mezcla basada en la fracción molar y la constante de cada polvo.", "A mixture rate constant based on mole fraction and each powder's rate constant is proposed."),
    ("El contenido de cal gobierna la rapidez de la co-inyección, sobre todo en la primera mitad: más cal, mayor vida media.", "Lime content governs co-injection speed, especially in the first half: more lime, longer half-life."),
    ("Para acelerar la desulfuración conviene reducir la cal en la mezcla; como es el polvo más barato, la decisión requiere un análisis económico, técnico y de productividad en planta.",
     "To speed up desulfurization, lime in the mix should be reduced; since it is the cheapest powder, the decision requires an economic, technical and productivity analysis at plant level."),
    ("5 · Simulación CFD 3D", "5 · 3D CFD simulation"), ("El baño por dentro: explora la simulación 3D", "Inside the bath: explore the 3D simulation"),
    ("<h3>La CFD del artículo</h3>", "<h3>The paper's CFD</h3>"),
    ("Para comprobar el supuesto de tanque bien agitado, el artículo simula la olla en 2D con Fluent 6.1: flujo transitorio e isotérmico, modelo VOF para las dos fases y turbulencia k-ε estándar. El gas sale por dos toberas a 45° con la velocidad de burbuja del modelo, con <var>k</var> = 0.01 <var>v</var><sub>b</sub>² a la entrada y <var>ε</var> calculada con el diámetro de la tobera. A los 5 s las burbujas suben junto a la lanza y muchas se abren hacia las paredes en la parte alta (figura 3), y las líneas de corriente muestran agitación hasta el fondo de la olla (figura 4).",
     "To check the well-stirred tank assumption, the paper simulates the ladle in 2D with Fluent 6.1: transient, isothermal flow, the VOF model for the two phases and standard k-ε turbulence. Gas leaves two nozzles at 45° at the model's bubble velocity, with <var>k</var> = 0.01 <var>v</var><sub>b</sub>² at the inlet and <var>ε</var> computed from the nozzle diameter. At 5 s the bubbles rise next to the lance and many spread toward the walls in the upper part (figure 3), and the streamlines show stirring down to the bottom of the ladle (figure 4)."),
    ("<h3>La CFD de este gemelo</h3>", "<h3>This twin's CFD</h3>"),
    ("Aquí la misma olla se simuló completa en 3D con <b>OpenFOAM</b>. Con burbujas de poco más de 1 mm en un baño de más de 2.5 m de alto, el gas se trata como una fase continua que convive con el arrabio (modelo Euler–Euler), en lugar de seguir cada interfase como en VOF; la turbulencia es k-ε de mezcla. Se respetan la profundidad de la lanza, las dos toberas de 20 mm a 45°, la velocidad de salida y los valores de <var>k</var> y <var>ε</var> de entrada del artículo.",
     "Here the same ladle was simulated in full 3D with <b>OpenFOAM</b>. With bubbles just over 1 mm in a bath more than 2.5 m deep, the gas is treated as a continuous phase coexisting with the metal (Euler–Euler model) instead of tracking every interface as in VOF; turbulence is mixture k-ε. The lance depth, the two 20 mm nozzles at 45°, the exit velocity and the paper's inlet <var>k</var> and <var>ε</var> are kept."),
    ("Cada caso simula 60 s de flujo y los campos se promedian entre 20 s y 60 s, cuando la circulación ya se estableció. El argón sube junto a la lanza y, al llegar a la superficie, se abre hacia las paredes; el arrabio baja por los costados y forma un gran lazo de recirculación a cada lado de la lanza que llega hasta el fondo: el mismo cuadro de las figuras 3 y 4.",
     "Each case simulates 60 s of flow and the fields are averaged between 20 s and 60 s, once circulation is established. Argon rises next to the lance and, at the surface, spreads toward the walls; the metal sinks along the sides and forms a large recirculation loop on each side of the lance reaching the bottom: the same picture as figures 3 and 4."),
    ("<dt>Geometría</dt><dd>olla Ø 3.2 m, baño de 2.63 m</dd>", "<dt>Geometry</dt><dd>ladle Ø 3.2 m, 2.63 m bath</dd>"),
    ("<dt>Lanza</dt><dd>0.2 m, 2 toberas de 20 mm a 45°</dd>", "<dt>Lance</dt><dd>0.2 m, 2 nozzles of 20 mm at 45°</dd>"),
    ("<dt>Malla fina</dt><dd>515&#8239;520 celdas</dd>", "<dt>Fine mesh</dt><dd>515&#8239;520 cells</dd>"),
    ("<dt>Argón</dt><dd>burbujas de 1.17 mm · 0.5 L/s</dd>", "<dt>Argon</dt><dd>1.17 mm bubbles · 0.5 L/s</dd>"),
    ("<dt>Arrabio</dt>", "<dt>Hot metal</dt>"), ("<dt>Turbulencia</dt><dd>k-ε de mezcla</dd>", "<dt>Turbulence</dt><dd>mixture k-ε</dd>"),
    ("<dt>Tiempo</dt><dd>60 s por caso, promedio de 20 a 60 s</dd>", "<dt>Time</dt><dd>60 s per case, averaged 20–60 s</dd>"),
    ("<dt>Cómputo</dt><dd>12 corridas, local, 8 núcleos</dd>", "<dt>Compute</dt><dd>12 runs, local, 8 cores</dd>"),
    ('aria-label="Explorador 3D del flujo en la olla; arrastra para girar, rueda para acercar"', 'aria-label="3D flow explorer of the ladle; drag to rotate, scroll to zoom"'),
    ("Cargando el flujo 3D…", "Loading the 3D flow…"), ('aria-label="Cerrar recorrido"', 'aria-label="Close tour"'),
    ('id="tour-ant">Anterior</button>', 'id="tour-ant">Previous</button>'), ('id="tour-sig">Siguiente</button>', 'id="tour-sig">Next</button>'),
    ('<label for="ex-caso">Caso de la simulación</label>', '<label for="ex-caso">Simulation case</label>'),
    ('id="ex-recorrido">Recorrido guiado</button>', 'id="ex-recorrido">Guided tour</button>'), ('id="ex-tinte">Prueba de mezclado</button>', 'id="ex-tinte">Mixing test</button>'),
    ('id="ex-completa">Pantalla completa</button>', 'id="ex-completa">Full screen</button>'), ('id="fig1-completa">Pantalla completa</button>', 'id="fig1-completa">Full screen</button>'),
    ("<legend>Capas</legend>", "<legend>Layers</legend>"), ("> Corte vertical</label>", "> Vertical cut</label>"), ("> Rebanada horizontal</label>", "> Horizontal slice</label>"),
    ("> Pluma de argón <small", "> Argon plume <small"), ("> Partículas</label>", "> Particles</label>"), ("> Líneas de corriente</label>", "> Streamlines</label>"),
    ("<span>Giro del corte</span>", "<span>Cut rotation</span>"), ("<span>Altura de la rebanada</span>", "<span>Slice height</span>"),
    ('id="ex-soltar">Soltar partículas en las toberas</button>', 'id="ex-soltar">Release particles at the nozzles</button>'), ('aria-pressed="true">Pausar giro</button>', 'aria-pressed="true">Pause rotation</button>'),
    ("Flujo promedio entre 20 s y 60 s de cada caso. El color es la rapidez del arrabio; la pluma azulada es el argón; las partículas siguen la velocidad 3D calculada, 10 veces más rápido. Pasa el cursor sobre un corte para leer la rapidez y el gas en ese punto, y haz clic para soltar ahí un tinte. La prueba de mezclado transporta el tinte solo con el flujo promedio, sin la dispersión turbulenta: muestra por dónde viaja el metal y dónde se estanca (la zona lenta del fondo junto a la pared), no el tiempo real de mezclado, que la turbulencia acorta mucho.",
     "Average flow between 20 s and 60 s of each case. Color is the hot metal speed; the bluish plume is the argon; particles follow the computed 3D velocity, 10 times faster. Hover over a cut to read the speed and gas at that point, and click to release dye there. The mixing test carries the dye with the average flow only, without turbulent dispersion: it shows where the metal travels and where it stagnates (the slow region near the bottom by the wall), not the actual mixing time, which turbulence shortens considerably."),
    ("<h3>Barrido: caudal de gas × profundidad de lanza</h3>", "<h3>Sweep: gas flow × lance depth</h3>"),
    ('aria-label="Medida"', 'aria-label="Measure"'), ('aria-pressed="true">media</button>', 'aria-pressed="true">mean</button>'), ('aria-pressed="false">percentil 95</button>', 'aria-pressed="false">95th percentile</button>'),
    ("Rapidez del arrabio en el corte por las toberas, malla media. Hundir más la lanza da más altura a la pluma y acelera la circulación; duplicar el gas también, en menor medida.",
     "Hot metal speed in the cut through the nozzles, medium mesh. A deeper lance gives the plume more height and speeds up circulation; doubling the gas does too, to a lesser extent."),
    ("<h3>Estudio de malla</h3>", "<h3>Mesh study</h3>"), ("<th>Malla</th><th>Celdas</th><th>v media</th><th>v p95</th>", "<th>Mesh</th><th>Cells</th><th>mean v</th><th>v p95</th>"),
    ("Caso base con caudal y lanza del artículo. La malla media basta para la circulación global, con la que se corrió el barrido; la fina resuelve mejor la pluma y se usó para el caso base con toberas del video.",
     "Base case with the paper's gas flow and lance. The medium mesh is enough for the overall circulation and was used for the sweep; the fine mesh resolves the plume better and was used for the base case with nozzles in the video."),
    ("<summary>Supuestos de la simulación</summary>", "<summary>Simulation assumptions</summary>"),
    ("Tomado del artículo: masa de 150 t, profundidad de lanza, dos toberas de 20 mm a 45°, diámetro de burbuja, densidad y viscosidad del arrabio, k y ε de entrada. Supuesto aquí por ser típico de una olla de 150 t: diámetro de 3.2 m, lanza cuadrada de 0.2 m, 0.4 m de espacio libre, tensión superficial de 1.7 N/m y proceso isotérmico a 1350 °C.",
     "From the paper: 150 t mass, lance depth, two 20 mm nozzles at 45°, bubble diameter, hot metal density and viscosity, inlet k and ε. Assumed here as typical of a 150 t ladle: 3.2 m diameter, 0.2 m square lance, 0.4 m freeboard, 1.7 N/m surface tension and an isothermal process at 1350 °C."),
    ("6 · Cómo se hizo", "6 · How it was made"), ("<h2>Del artículo al gemelo</h2>", "<h2>From the paper to the twin</h2>"),
    ("<b>Reproducir el modelo.</b> Las ecuaciones 6 a 9, 15 y 16 se programaron en Python con los valores de las tablas 1 a 3 y se comprobaron contra los resultados publicados: velocidad de burbuja, tiempo de residencia, constante de la cal, azufre final y las constantes de las cinco mezclas.",
     "<b>Reproduce the model.</b> Equations 6 to 9, 15 and 16 were programmed in Python with the values of tables 1 to 3 and checked against the published results: bubble velocity, residence time, lime rate constant, final sulfur and the constants of the five mixtures."),
    ("<b>Llevarlo al navegador.</b> El mismo modelo corre en JavaScript dentro de esta página; se comparó contra la versión de Python en 28 puntos, sin diferencias.",
     "<b>Bring it to the browser.</b> The same model runs in JavaScript inside this page; it was compared against the Python version at 28 points, with no differences."),
    ("<b>Simular el flujo.</b> Doce corridas 3D en OpenFOAM: un estudio de malla (gruesa, media y fina), un barrido de 3 caudales de gas × 3 profundidades de lanza y el caso base en malla fina con las toberas modeladas. Corrieron en una computadora personal, con pausa y reanudación automáticas.",
     "<b>Simulate the flow.</b> Twelve 3D runs in OpenFOAM: a mesh study (coarse, medium and fine), a sweep of 3 gas flows × 3 lance depths and the base case on the fine mesh with the nozzles modeled. They ran on a personal computer, with automatic pause and resume."),
    ("<b>Extraer los campos.</b> ParaView y Python sacan de cada corrida el corte vertical por la lanza, el flujo promedio y las líneas de corriente.",
     "<b>Extract the fields.</b> ParaView and Python take from each run the vertical cut through the lance, the average flow and the streamlines."),
    ("<b>Visualizar.</b> Blender (Cycles) arma el corte de la olla con esos campos; three.js muestra las líneas de corriente en 3D en esta página.",
     "<b>Visualize.</b> Blender (Cycles) builds the ladle cut from those fields; three.js shows the flow in 3D on this page."),
    ("<h3>Alcances</h3>", "<h3>Scope</h3>"),
    ("Como en el artículo, el proceso es isotérmico; la ec. 5 no se usa porque requiere <var>k</var><sub>0</sub> y <var>E</var><sub>a</sub>.", "As in the paper, the process is isothermal; eq. 5 is not used because it needs <var>k</var><sub>0</sub> and <var>E</var><sub>a</sub>."),
    ("<li>La escoria no se modela.</li>", "<li>The slag is not modeled.</li>"),
    ("La CFD resuelve el flujo del gas y del metal, no la química: las curvas de azufre salen del modelo publicado.", "The CFD resolves the gas and metal flow, not the chemistry: the sulfur curves come from the published model."),
    ("El diámetro de la olla, la sección de la lanza y algunas propiedades no vienen en el artículo; se tomaron valores típicos de una olla de 150 t (ver los supuestos en la sección 5).",
     "The ladle diameter, the lance cross-section and some properties are not given in the paper; typical values for a 150 t ladle were used (see the assumptions in section 5)."),
    ('<p class="antetitulo">Créditos</p>', '<p class="antetitulo">Credits</p>'),
    ("<b>Basado en:</b> Barrón, M. A., Hilerio, I. y Medina, D. Y. (2015).", "<b>Based on:</b> Barrón, M. A., Hilerio, I. and Medina, D. Y. (2015)."),
    ("<b>Autores del modelo original:</b> Miguel A. Barrón, Isaías Hilerio y Dulce Y. Medina, Departamento de Materiales, Universidad Autónoma Metropolitana, Unidad Azcapotzalco, Ciudad de México.",
     "<b>Authors of the original model:</b> Miguel A. Barrón, Isaías Hilerio and Dulce Y. Medina, Department of Materials, Universidad Autónoma Metropolitana, Azcapotzalco campus, Mexico City."),
    ("<b>Licencia:</b> el artículo se publica bajo Creative Commons Atribución 4.0 (", "<b>License:</b> the paper is published under Creative Commons Attribution 4.0 ("),
    ('href="https://creativecommons.org/licenses/by/4.0/deed.es"', 'href="https://creativecommons.org/licenses/by/4.0/"'),
    ("), que permite reutilizar su modelo y sus figuras con crédito.", "), which allows reusing its model and figures with credit."),
    ("<b>Datos citados por el artículo:</b> validación con Oeters (1989), <i>Metallurgy of Steelmaking</i>; constante del carburo de calcio de Zhao (1992); constante del magnesio de Irons y Guthrie (1981).",
     "<b>Data cited by the paper:</b> validation against Oeters (1989), <i>Metallurgy of Steelmaking</i>; calcium carbide constant from Zhao (1992); magnesium constant from Irons and Guthrie (1981)."),
    ("<b>Esta reinterpretación:</b> gemelo digital interactivo elaborado por Gersain Barrón con software libre (OpenFOAM, ParaView, Python, Blender, three.js). Los cortes, burbujas y líneas de corriente provienen de simulaciones CFD propias en OpenFOAM con los parámetros del artículo; las curvas de azufre provienen del modelo publicado.",
     "<b>This reinterpretation:</b> interactive digital twin by Gersain Barrón using open-source software (OpenFOAM, ParaView, Python, Blender, three.js). The cuts, bubbles and streamlines come from our own OpenFOAM CFD simulations with the paper's parameters; the sulfur curves come from the published model."),
    ('<a href="#metodo">Método</a>', '<a href="#metodo">Method</a>'),
]
faltan = []
for a, b in PARES:
    if a in h:
        h = h.replace(a, b)
    elif b not in h:
        faltan.append(a[:70])
# selector de idioma en la barra
h = h.replace('<a href="index-en.html" lang="en" class="idioma">EN</a>', '<a href="index.html" lang="es" class="idioma">ES</a>')
(W / "index-en.html").write_text(h, encoding="utf-8")

# texto que quedo en espanol
texto = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", "\n", h, flags=re.S)
sospechas = [l.strip() for l in texto.split("\n") if re.search(r"[áéíóúñ¿]|\b(el|la|los|las|del|con|para|que|por)\b", l) and not re.search(r"Barrón|Isaías|Autónoma|Azcapotzalco|México|Medina|Hilerio", l)]
if faltan or sospechas:
    print("NO ENCONTRADOS:", *faltan, sep="\n  ")
    print("POSIBLE ESPANOL:", *sospechas[:40], sep="\n  ")
    sys.exit(1)
print("index-en.html listo")
