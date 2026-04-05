import unittest

from main import HTML_PAGE, MIN_PRESSURE_ATM


class FrontendContractTests(unittest.TestCase):
    def test_pressure_slider_enforces_supported_minimum(self) -> None:
        self.assertIn(f'id="pressure" type="range" min="{MIN_PRESSURE_ATM}" max="1.2"', HTML_PAGE)
        self.assertIn("const MIN_PRESSURE = 0.001;", HTML_PAGE)
        self.assertIn("function clampPressure(pressureAtm)", HTML_PAGE)
        self.assertIn("Number(v) < 0.01 ? Number(v).toFixed(3) : Number(v).toFixed(2)", HTML_PAGE)

    def test_material_density_control_can_expand_for_dense_historic_presets(self) -> None:
        self.assertIn("function syncMaterialDensityLimit(materialDensity)", HTML_PAGE)
        self.assertIn("Math.max(defaultMaterialDensityMax, roundedMax)", HTML_PAGE)

    def test_plot_bounds_keep_at_least_the_requested_axes_but_do_not_clip_presets_by_default(self) -> None:
        self.assertIn("return state.stableBounds || state.focusedBounds || { maxX: 2400, maxY: 850 };", HTML_PAGE)

    def test_historic_guns_use_stable_per_gun_plot_bounds(self) -> None:
        self.assertIn("function activePlotBounds()", HTML_PAGE)
        self.assertIn('body: JSON.stringify({ ...state.params, currentGun: state.currentGun })', HTML_PAGE)

    def test_selected_gun_can_be_customized_without_leaving_gun_context(self) -> None:
        self.assertIn("presetModified: false", HTML_PAGE)
        self.assertIn("state.presetModified = !paramsMatch(state.params, historicalGuns[state.currentGun].params);", HTML_PAGE)
        self.assertIn('historicalGuns[state.currentGun].name}${state.presetModified ? " custom" : ""}', HTML_PAGE)

    def test_resize_redraws_without_rerunning_physics(self) -> None:
        self.assertIn("async function recalculatePhysics()", HTML_PAGE)
        self.assertIn("function redrawDisplay()", HTML_PAGE)
        self.assertIn('window.addEventListener("resize", () => {', HTML_PAGE)

    def test_launch_controls_expose_projectile_shape_toggle(self) -> None:
        self.assertIn('id="shapeSphereBtn"', HTML_PAGE)
        self.assertIn('id="shapeShellBtn"', HTML_PAGE)
        self.assertIn("function setProjectileShape(shape, options = {})", HTML_PAGE)

    def test_header_exposes_flight_time_indicators(self) -> None:
        self.assertIn('id="hero-ideal-time"', HTML_PAGE)
        self.assertIn('id="hero-drag-time"', HTML_PAGE)
        self.assertIn('state.ideal.metrics.flightTime.toFixed(2)', HTML_PAGE)
        self.assertIn('state.drag.metrics.flightTime.toFixed(2)', HTML_PAGE)
        self.assertIn('id="hero-impact-reynolds"', HTML_PAGE)
        self.assertIn('state.drag.aero.impactReynolds.toFixed(0)', HTML_PAGE)
        self.assertNotIn('id="hero-ideal-speed"', HTML_PAGE)

    def test_frontend_uses_python_simulation_endpoint(self) -> None:
        self.assertIn('fetch("/api/simulate"', HTML_PAGE)
        self.assertIn('"X-CSRF-Token": state.csrfToken', HTML_PAGE)
        self.assertIn('fetch("/session/bootstrap"', HTML_PAGE)
        self.assertIn("const BOOTSTRAP_CHALLENGE = __BOOTSTRAP_CHALLENGE__;", HTML_PAGE)
        self.assertNotIn("function simulateDrag(params)", HTML_PAGE)
        self.assertNotIn("function simulateIdeal(params)", HTML_PAGE)

    def test_historic_library_includes_siege_engines(self) -> None:
        self.assertIn("Counterweight trebuchet", HTML_PAGE)
        self.assertIn("Mangonel / traction catapult", HTML_PAGE)
        self.assertIn("Ballista", HTML_PAGE)
