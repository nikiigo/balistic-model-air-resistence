import unittest

from ballistics.constants import MAX_PRESSURE_ATM, MAX_SPEED, MIN_PRESSURE_ATM
from ballistics.web.templates import HTML_PAGE


class FrontendContractTests(unittest.TestCase):
    def test_pressure_slider_enforces_supported_minimum(self) -> None:
        self.assertIn(f'id="pressure" type="range" min="{MIN_PRESSURE_ATM}" max="{MAX_PRESSURE_ATM}"', HTML_PAGE)
        self.assertIn("const MIN_PRESSURE = 0.001;", HTML_PAGE)
        self.assertIn("function clampPressure(pressureAtm)", HTML_PAGE)
        self.assertIn("Number(v) < 0.01 ? Number(v).toFixed(3) : Number(v).toFixed(2)", HTML_PAGE)

    def test_speed_slider_matches_backend_limit(self) -> None:
        self.assertIn(f'id="speed" type="range" min="5" max="{int(MAX_SPEED)}"', HTML_PAGE)

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

    def test_frontend_shows_recalculation_status(self) -> None:
        self.assertIn('id="calcStatus"', HTML_PAGE)
        self.assertIn('aria-live="polite"', HTML_PAGE)
        self.assertIn('updateCalculationStatus("Recalculating trajectory...", "busy");', HTML_PAGE)
        self.assertIn('updateCalculationStatus("Unlock simulator to calculate", "blocked");', HTML_PAGE)
        self.assertIn('calcStatusEl.classList.add("visible");', HTML_PAGE)
        self.assertIn("function hideCalculationStatus()", HTML_PAGE)
        self.assertIn("hideCalculationStatus();", HTML_PAGE)

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

    def test_homepage_defaults_to_napoleon_gun_mode(self) -> None:
        self.assertIn('currentGun: "napoleon"', HTML_PAGE)
        self.assertIn("angle: 12,", HTML_PAGE)
        self.assertIn("speed: 439,", HTML_PAGE)
        self.assertIn("diameter: 0.117,", HTML_PAGE)
        self.assertIn('setGunMode("napoleon");', HTML_PAGE)
        self.assertNotIn("syncControls(defaults);", HTML_PAGE)

    def test_selecting_a_round_shot_preset_normalizes_shape_back_to_sphere(self) -> None:
        self.assertIn('projectileShape: "sphere"', HTML_PAGE)
        self.assertIn('ballisticCoefficient: 0', HTML_PAGE)
        self.assertIn("syncControls(normalizedParams);", HTML_PAGE)

    def test_metric_cards_render_in_requested_order(self) -> None:
        ideal_range_index = HTML_PAGE.index('metricCard("Ideal range"')
        ideal_max_height_index = HTML_PAGE.index('metricCard("Ideal max height"')
        time_step_index = HTML_PAGE.index('metricCard("Time step"')
        drag_max_height_index = HTML_PAGE.index('metricCard("Drag max height"')
        drag_range_index = HTML_PAGE.index('metricCard("Drag range"')
        range_loss_index = HTML_PAGE.index('metricCard("Range loss to drag"')
        self.assertLess(ideal_range_index, ideal_max_height_index)
        self.assertLess(ideal_max_height_index, time_step_index)
        self.assertLess(time_step_index, drag_range_index)
        self.assertLess(drag_range_index, drag_max_height_index)
        self.assertLess(drag_max_height_index, range_loss_index)

    def test_historic_library_includes_siege_engines(self) -> None:
        self.assertIn("Counterweight trebuchet", HTML_PAGE)
        self.assertIn("Mangonel / traction catapult", HTML_PAGE)
        self.assertIn("Ballista", HTML_PAGE)
        self.assertIn("M1841 6-pounder gun", HTML_PAGE)
