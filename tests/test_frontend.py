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

    def test_historic_hover_panel_is_anchored_higher_on_desktop(self) -> None:
        self.assertIn("top: clamp(-120px, -10vh, -56px);", HTML_PAGE)
        self.assertIn('class="gun-hover-body"', HTML_PAGE)
        self.assertIn('class="gun-hover-media"', HTML_PAGE)
        self.assertNotIn('class="gun-hover-head"', HTML_PAGE)
        self.assertIn(".gun-copy {\n      display: block;", HTML_PAGE)
        self.assertIn(".gun-specs {\n      display: block;", HTML_PAGE)
        self.assertIn(".gun-hover-media {\n      width: 100%;", HTML_PAGE)
        self.assertIn("aspect-ratio: 4 / 3;", HTML_PAGE)

    def test_frontend_historical_guns_reuse_backend_param_map(self) -> None:
        self.assertIn("const presets = ", HTML_PAGE)
        self.assertIn("const historicalGunParams = ", HTML_PAGE)
        self.assertIn("params: historicalGunParams.ballista", HTML_PAGE)
        self.assertIn("params: historicalGunParams.napoleon", HTML_PAGE)

    def test_ballista_and_mangonel_use_updated_local_images(self) -> None:
        self.assertIn('/assets/guns/roman-ballista-alesia.jpg', HTML_PAGE)
        self.assertIn('/assets/guns/mauvezin-mangonel.jpg', HTML_PAGE)

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

    def test_header_exposes_quick_guide_dialog(self) -> None:
        self.assertIn('class="stat help-trigger" id="guideBtn"', HTML_PAGE)
        self.assertIn('<span class="help-glyph">?</span>', HTML_PAGE)
        self.assertIn(".stat-strip {\n      display: grid;\n      gap: clamp(8px, 0.9vw, 12px);\n      grid-template-columns: repeat(9, minmax(0, 1fr));", HTML_PAGE)
        self.assertIn(".hero-title {\n      display: flex;\n      align-items: center;\n      gap: clamp(8px, 0.8vw, 10px);\n      flex-wrap: nowrap;", HTML_PAGE)
        self.assertIn(".help-trigger {\n      min-width: 34px;", HTML_PAGE)
        self.assertIn("border-radius: var(--hero-stat-radius);", HTML_PAGE)
        self.assertIn("background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(255,255,255,0.4));", HTML_PAGE)
        self.assertIn(".help-glyph {\n      display: block;", HTML_PAGE)
        self.assertIn("color: var(--accent);", HTML_PAGE)
        self.assertIn("font-size: 2.45rem;", HTML_PAGE)
        self.assertIn("font-weight: 950;", HTML_PAGE)
        self.assertIn("line-height: 0.78;", HTML_PAGE)
        self.assertIn("transform: translateY(-1px) scale(1.08);", HTML_PAGE)
        self.assertIn(".help-trigger:hover {\n      border-color: rgba(182, 70, 42, 0.18);", HTML_PAGE)
        self.assertIn(".help-trigger:hover .help-glyph {\n      color: #fff7f0;", HTML_PAGE)
        scale_card_index = HTML_PAGE.index('class="stat scale-stat"')
        guide_button_index = HTML_PAGE.index('class="stat help-trigger" id="guideBtn"')
        self.assertLess(scale_card_index, guide_button_index)
        self.assertIn('id="guideOverlay" role="dialog" aria-modal="true"', HTML_PAGE)
        self.assertIn("Quick Guide", HTML_PAGE)
        self.assertIn("The goal of this project is to demonstrate how real-world physical factors affect ballistic modeling results.", HTML_PAGE)
        self.assertIn("Use the controls to change launch angle, muzzle velocity, projectile diameter, material density, air temperature, air pressure, and integration time step.", HTML_PAGE)
        self.assertIn("compressibility effects via Mach number", HTML_PAGE)
        self.assertIn("environmental variables can significantly change projectile trajectory", HTML_PAGE)
        self.assertIn("Quick Start", HTML_PAGE)
        self.assertIn("Start by choosing a historic launcher on the left or stay in manual setup if you want to build a shot from scratch.", HTML_PAGE)
        self.assertIn("Try changing only one environmental parameter at a time, such as air pressure or temperature, to see how strongly the trajectory responds.", HTML_PAGE)
        self.assertIn("try to find the launch angle that gives the longest drag-limited range in a real atmosphere", HTML_PAGE)
        self.assertIn("Round Shot Model", HTML_PAGE)
        self.assertIn("Shell Model", HTML_PAGE)
        self.assertIn("Shell projectiles use a G7 ballistic-coefficient model with density-scaled drag.", HTML_PAGE)
        self.assertIn("It does not use the round-shot sphere `Cd(Re, Ma)` law as the primary shell drag model.", HTML_PAGE)
        self.assertIn("function openGuide()", HTML_PAGE)
        self.assertIn("function closeGuide()", HTML_PAGE)

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
