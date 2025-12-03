'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CircleMarker, MapContainer, Polygon, Popup, TileLayer, Tooltip, useMap, Marker } from 'react-leaflet';
import type { LeafletMouseEvent, LatLngBoundsExpression } from 'leaflet';
import L, { divIcon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw';
import 'leaflet-draw/dist/leaflet.draw.css';
import { Layers, MapPin as MapPinIcon, Shapes, Trash2 } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import { Select } from '@/components/UI/Select';
import { COLOR_PALETTE, LAYER_LABELS, MAP_CONFIG, PIN_TYPE_OPTIONS } from '@/lib/constants';
import type {
  AdvancedOptions,
  AnalysisResult,
  DrawingMode,
  LayerKey,
  LatLng,
  LocationSelection,
  MapPin,
  PinTypeOption,
} from '@/lib/types';
import { calculatePolygonMetrics } from '@/lib/mapUtils';
import { RiskHeatmap } from './RiskHeatmap';

const polygonOptions: L.DrawOptions.PolygonOptions = {
  showArea: true,
  allowIntersection: false,
  shapeOptions: {
    color: COLOR_PALETTE.primary,
    weight: 2,
    fillOpacity: 0.15,
  },
};

const pinTypeMap = Object.fromEntries(PIN_TYPE_OPTIONS.map((option) => [option.id, option]));

interface BaseLayerOption {
  id: string;
  label: string;
  description: string;
  url: string;
  attribution: string;
}

const BASE_LAYER_OPTIONS: BaseLayerOption[] = [
  {
    id: 'standard',
    label: 'OpenStreetMap',
    description: 'Default street map view',
    url: MAP_CONFIG.tileLayer,
    attribution: MAP_CONFIG.attribution,
  },
  {
    id: 'terrain',
    label: 'Terrain',
    description: 'Topographic map with terrain',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution:
      'Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)',
  },
  {
    id: 'satellite',
    label: 'Satellite',
    description: 'Esri world imagery',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution:
      'Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community.',
  },
];

export interface MapViewContentProps {
  location: LocationSelection | null;
  result: AnalysisResult | null;
  advancedOptions: AdvancedOptions;
  selectedZoneId: string | null;
  drawingMode: DrawingMode;
  selectedPinType: string;
  pins: MapPin[];
  onToggleLayer: (layer: LayerKey) => void;
  onDrawingModeChange: (mode: DrawingMode) => void;
  onPolygonComplete: (polygon: LatLng[]) => void;
  onClearShapes: () => void;
  onPinTypeChange: (typeId: string) => void;
  onPinPlaced: (pin: { position: LatLng; typeId: string }) => void;
  onPinRemove: (pinId: string) => void;
  onClearPins: () => void;
  onZoneClick: (zoneId: string) => void;
  onNewSession?: () => void;
}

export function MapViewContent(props: MapViewContentProps) {
  const {
    location,
    result,
    advancedOptions,
    drawingMode,
    selectedPinType,
    pins,
    onToggleLayer,
    onDrawingModeChange,
    onPolygonComplete,
    onClearShapes,
    onPinTypeChange,
    onPinPlaced,
    onPinRemove,
    onClearPins,
    onZoneClick,
    onNewSession,
  } = props;

  const mapRef = useRef<L.Map | null>(null);
  const drawHandlerRef = useRef<L.Draw.Polygon | null>(null);
  const drawnLayersRef = useRef<L.FeatureGroup | null>(null);

  const layerOptions = useMemo(
    () =>
      (Object.entries(LAYER_LABELS) as Array<[LayerKey, string]>).map(([key, label]) => ({
        key,
        label,
      })),
    []
  );

  const [baseLayerId, setBaseLayerId] = useState<string>(BASE_LAYER_OPTIONS[0].id);

  const activeBaseLayer = useMemo(() => {
    const option = BASE_LAYER_OPTIONS.find((layer) => layer.id === baseLayerId);
    return option ?? BASE_LAYER_OPTIONS[0];
  }, [baseLayerId]);

  const polygonSummary = useMemo(() => calculatePolygonMetrics(location?.polygon), [location]);
  const numberFormatter = useMemo(
    () => new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }),
    []
  );

  // Clear temporary drawn layers when React renders the polygon
  useEffect(() => {
    if (location?.type === 'custom' && location.polygon?.length && drawnLayersRef.current) {
      console.log('🧹 Clearing temporary drawn layers, React polygon is now rendered');
      drawnLayersRef.current.clearLayers();
    }
  }, [location]);

  const handleStartPolygon = useCallback(() => {
    onDrawingModeChange('polygon');
  }, [onDrawingModeChange]);

  const handleFinishPolygon = useCallback(() => {
    // Disable the current drawing handler and exit polygon mode
    // The polygon will have already been captured in the CREATED event
    drawHandlerRef.current?.disable();
    drawHandlerRef.current = null;
    onDrawingModeChange('none');
  }, [onDrawingModeChange]);

  useEffect(() => {
    const mapInstance = mapRef.current;
    if (!mapInstance) {
      return;
    }

    // Create a feature group to hold drawn layers if it doesn't exist
    if (!drawnLayersRef.current) {
      drawnLayersRef.current = new L.FeatureGroup();
      mapInstance.addLayer(drawnLayersRef.current);
      console.log('🗂️ Created drawnLayersRef feature group');
    }

    if (drawingMode === 'polygon') {
      drawHandlerRef.current?.disable();
      drawHandlerRef.current = new L.Draw.Polygon(
        mapInstance as unknown as L.DrawMap,
        polygonOptions
      );
      mapInstance.getContainer().style.cursor = 'crosshair';

      // Disable double-click zoom during polygon drawing
      mapInstance.doubleClickZoom.disable();
      console.log('🔒 Double-click zoom disabled');

      drawHandlerRef.current.enable();
      console.log('✏️ Polygon drawing enabled');
      console.log('📋 Listening for these events:', L.Draw.Event.CREATED, L.Draw.Event.DRAWSTART, L.Draw.Event.DRAWVERTEX);

      // Add more event listeners for debugging
      mapInstance.on(L.Draw.Event.DRAWSTART, () => {
        console.log('🎬 DRAWSTART event fired');
      });

      mapInstance.on(L.Draw.Event.DRAWVERTEX, (e: L.LeafletEvent) => {
        const drawEvent = e as L.DrawEvents.DrawVertex;
        const layerCount = drawEvent.layers?.getLayers().length || 0;
        console.log('📍 DRAWVERTEX event fired, layers:', layerCount);

        // Store the vertices as they're drawn
        if (drawEvent.layers) {
          const layers = drawEvent.layers.getLayers() as L.Marker[];
          const points = layers.map(marker => {
            const latLng = marker.getLatLng();
            return { lat: latLng.lat, lng: latLng.lng };
          });
          // Store in a closure variable
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (drawHandlerRef.current as any).__capturedPoints = points;
          console.log('💾 Captured', points.length, 'points');
        }
      });

      mapInstance.on(L.Draw.Event.DRAWSTOP, () => {
        console.log('🛑 DRAWSTOP event fired - executing handler');
        // Small delay to let Leaflet finish processing
        setTimeout(() => {
          console.log('⏱️ Timeout executed, checking markers');
          const handler = drawHandlerRef.current;
          if (!handler) {
            console.log('❌ No handler reference');
            return;
          }

          // First try the captured points from DRAWVERTEX events
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const capturedPoints = (handler as any).__capturedPoints;
          console.log('💾 Captured points:', capturedPoints?.length || 0);

          // Then try the internal marker array
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const markers = (handler as any)._markers;
          console.log('🔍 Handler _markers:', markers?.length || 0);

          // Try the poly property which holds the temporary polyline
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const poly = (handler as any)._poly;
          console.log('🗺️ Handler _poly:', poly ? 'exists' : 'null');

          let polygon: { lat: number; lng: number }[] | null = null;

          if (capturedPoints && capturedPoints.length >= 3) {
            console.log('✅ Using captured points');
            polygon = capturedPoints;
          } else if (markers && markers.length >= 3) {
            console.log('✅ Using _markers');
            const latLngs = markers.map((marker: L.Marker) => marker.getLatLng());
            polygon = latLngs.map((latLng: L.LatLng) => ({
              lat: latLng.lat,
              lng: latLng.lng
            }));
          } else if (poly) {
            // Try getting points from the polyline
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const latLngs = (poly as any).getLatLngs?.();
            console.log('🗺️ Poly latLngs:', latLngs?.length || 0);
            if (latLngs && latLngs.length >= 3) {
              console.log('✅ Using poly latLngs');
              polygon = latLngs.map((latLng: L.LatLng) => ({
                lat: latLng.lat,
                lng: latLng.lng
              }));
            }
          }

          if (polygon && polygon.length >= 3) {
            console.log('📦 Creating polygon with', polygon.length, 'points');

            // Add the polygon to drawnLayersRef so it persists
            const drawnLayers = drawnLayersRef.current;
            if (drawnLayers) {
              const latLngs = polygon.map(p => L.latLng(p.lat, p.lng));
              const polygonLayer = L.polygon(latLngs, {
                color: COLOR_PALETTE.primary,
                weight: 2,
                fillOpacity: 0.15,
              });
              drawnLayers.addLayer(polygonLayer);
              console.log('✨ Added manually created polygon to feature group');
            }

            console.log('✅ Manually completed polygon with', polygon.length, 'points');
            onPolygonComplete(polygon);
            onDrawingModeChange('none');
          } else {
            console.log('⚠️ Not enough points to create polygon (need 3+)');
          }
        }, 100);
      });

      return;
    }

    drawHandlerRef.current?.disable();
    drawHandlerRef.current = null;
    mapInstance.getContainer().style.cursor = '';

    // Re-enable double-click zoom
    mapInstance.doubleClickZoom.enable();
    console.log('🔓 Double-click zoom enabled');
    console.log('🛑 Drawing disabled');
  }, [drawingMode, onDrawingModeChange, onPolygonComplete]);

  useEffect(() => {
    const mapInstance = mapRef.current;
    if (!mapInstance) {
      return;
    }

    const handleCreated = (event: L.DrawEvents.Created) => {
      console.log('🎨 Draw event created:', event.layerType);

      if (event.layerType !== 'polygon') {
        return;
      }

      const layer = event.layer as L.Polygon;
      const latLngs = layer.getLatLngs()[0] as L.LatLng[] | undefined;

      console.log('📐 Polygon points:', latLngs?.length);

      if (!latLngs || latLngs.length === 0) {
        console.warn('⚠️ No points in polygon, removing layer');
        layer.remove();
        return;
      }

      const polygon = latLngs.map((latLng) => ({ lat: latLng.lat, lng: latLng.lng }));

      console.log('✅ Polygon completed with', polygon.length, 'points:', polygon);

      // Add to our feature group temporarily so it stays visible
      if (drawnLayersRef.current) {
        drawnLayersRef.current.addLayer(layer);
        console.log('➕ Added layer to feature group');
      } else {
        // Fallback: remove from map
        layer.remove();
      }

      onPolygonComplete(polygon);
      onDrawingModeChange('none');
    };

    const handleDrawStop = () => {
      console.log('🛑 DRAWSTOP event - checking for incomplete polygon');
      const handler = drawHandlerRef.current;
      if (!handler) {
        console.log('❌ No handler reference');
        return;
      }

      // Access the internal marker array to get the drawn points
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const markers = (handler as any)._markers;
      console.log('🔍 Handler markers:', markers?.length || 0);

      if (markers && markers.length >= 3) {
        console.log('📦 Found', markers.length, 'markers, creating polygon manually');
        const latLngs = markers.map((marker: L.Marker) => marker.getLatLng());
        const polygon = latLngs.map((latLng: L.LatLng) => ({
          lat: latLng.lat,
          lng: latLng.lng
        }));

        // Add the polygon to drawnLayersRef so it persists
        const drawnLayers = drawnLayersRef.current;
        if (drawnLayers) {
          const polygonLayer = L.polygon(latLngs, {
            color: COLOR_PALETTE.primary,
            weight: 2,
            fillOpacity: 0.15,
          });
          drawnLayers.addLayer(polygonLayer);
          console.log('✨ Added manually created polygon to feature group');
        }

        console.log('✅ Manually completed polygon with', polygon.length, 'points');
        onPolygonComplete(polygon);
        onDrawingModeChange('none');
      } else {
        console.log('⚠️ Not enough points to create polygon (need 3+)');
      }
    };

    const createdListener: L.LeafletEventHandlerFn = (event) => {
      handleCreated(event as L.DrawEvents.Created);
    };

    const drawStopListener: L.LeafletEventHandlerFn = () => {
      handleDrawStop();
    };

    mapInstance.on(L.Draw.Event.CREATED, createdListener);
    mapInstance.on(L.Draw.Event.DRAWSTOP, drawStopListener);

    console.log('👂 Registered CREATED and DRAWSTOP listeners');

    return () => {
      mapInstance.off(L.Draw.Event.CREATED, createdListener);
      mapInstance.off(L.Draw.Event.DRAWSTOP, drawStopListener);
      console.log('🔇 Removed event listeners');
    };
  }, [onDrawingModeChange, onPolygonComplete]);

  useEffect(() => {
    const mapInstance = mapRef.current;
    if (!mapInstance) {
      return;
    }

    if (drawingMode !== 'pin' || !selectedPinType) {
      mapInstance.getContainer().style.cursor =
        drawingMode === 'polygon' ? 'crosshair' : '';
      return;
    }

    const handleClick = (event: LeafletMouseEvent) => {
      onPinPlaced({
        position: { lat: event.latlng.lat, lng: event.latlng.lng },
        typeId: selectedPinType,
      });
    };

    mapInstance.getContainer().style.cursor = 'pointer';
    mapInstance.on('click', handleClick);

    return () => {
      mapInstance.getContainer().style.cursor = '';
      mapInstance.off('click', handleClick);
    };
  }, [drawingMode, onPinPlaced, selectedPinType]);

  return (
    <div className="relative h-screen flex-1" style={{ backgroundColor: COLOR_PALETTE.mapBackground }}>
      <MapContainer
        center={[MAP_CONFIG.center.lat, MAP_CONFIG.center.lng]}
        zoom={MAP_CONFIG.zoom}
        minZoom={MAP_CONFIG.minZoom}
        maxZoom={MAP_CONFIG.maxZoom}
        scrollWheelZoom
        className="h-full w-full"
        ref={mapRef}
        preferCanvas={true}
      >
        <TileLayer
          key={activeBaseLayer.id}
          attribution={activeBaseLayer.attribution}
          url={activeBaseLayer.url}
        />
        <FitBoundsEffect location={location} />
        {location?.type === 'custom' && location.polygon?.length ? (
          <>
            {console.log('🗺️ Rendering polygon with', location.polygon.length, 'points')}
            <Polygon
              pathOptions={{
                color: COLOR_PALETTE.primary,
                weight: 3,
                fillOpacity: 0.25,
              }}
              positions={location.polygon.map((point) => [point.lat, point.lng] as [number, number])}
            >
              {polygonSummary && (
                <Tooltip sticky direction="top" opacity={1} permanent>
                  <div className="space-y-1 text-xs text-white font-mono bg-[#1a1a1a] p-2 border border-white/20">
                    <p className="font-bold uppercase tracking-wider text-white/50">Custom Area</p>
                    <p>Points: {polygonSummary.points}</p>
                    <p>Area: {numberFormatter.format(polygonSummary.areaSqKm)} km²</p>
                    <p>Perimeter: {numberFormatter.format(polygonSummary.perimeterKm)} km</p>
                  </div>
                </Tooltip>
              )}
            </Polygon>
          </>
        ) : (
          <>
            {console.log('❌ No polygon to render. Location:', location?.type, 'Polygon length:', location?.polygon?.length)}
          </>
        )}
        {location?.point ? (
          <CircleMarker
            center={[location.point.lat, location.point.lng]}
            pathOptions={{
              color: COLOR_PALETTE.primary,
              fillColor: COLOR_PALETTE.primary,
              weight: 2,
              fillOpacity: 0.85,
            }}
            radius={6}
          />
        ) : null}

        {advancedOptions.enabledLayers.includes('riskHeatmap') && (
          <RiskHeatmap
            data={result?.geoJSON ?? null}
            displayThreshold={advancedOptions.displayThreshold}
            onSelectZone={(properties) => {
              const zoneId = String(properties?.id ?? properties?.gridId ?? '');
              if (zoneId) {
                onZoneClick(zoneId);
              }
            }}
          />
        )}

        {pins.map((pin) => {
          const config = pinTypeMap[pin.typeId];
          const color = config?.color ?? COLOR_PALETTE.primary;

          // Create a custom divIcon that looks like the CircleMarker but is accessible
          const icon = divIcon({
            className: 'bg-transparent',
            html: `<div style="
              background-color: ${color};
              width: 14px;
              height: 14px;
              border-radius: 50%;
              border: 2px solid ${color};
              opacity: 0.85;
              box-shadow: 0 0 0 1px white;
            "></div>`,
            iconSize: [14, 14],
            iconAnchor: [7, 7],
          });

          return (
            <Marker
              key={pin.id}
              position={[pin.position.lat, pin.position.lng]}
              icon={icon}
              keyboard={true}
              title={`${config?.label ?? 'Map pin'} at Lat ${pin.position.lat.toFixed(4)}, Lng ${pin.position.lng.toFixed(4)}`}
              alt={`${config?.label ?? 'Map pin'}`}
            >
              <Popup closeButton className="palantir-popup">
                <div className="space-y-2 text-white font-mono min-w-[200px]">
                  <div>
                    <p className="text-sm font-bold uppercase tracking-wider">{config?.label ?? 'Map pin'}</p>
                    {config?.description && (
                      <p className="text-[10px] text-white/60">{config.description}</p>
                    )}
                  </div>
                  <p className="text-[10px] text-white/50">
                    LAT {pin.position.lat.toFixed(4)} // LNG {pin.position.lng.toFixed(4)}
                  </p>
                  <button
                    type="button"
                    className="w-full border border-red-500/50 bg-red-900/20 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-red-400 transition hover:bg-red-900/40 hover:text-red-300"
                    onClick={() => onPinRemove(pin.id)}
                  >
                    Remove Pin
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      <MapToolbar
        drawingMode={drawingMode}
        selectedPinType={selectedPinType}
        pinOptions={PIN_TYPE_OPTIONS}
        pinsCount={pins.length}
        onModeChange={onDrawingModeChange}
        onStartPolygon={handleStartPolygon}
        onFinishPolygon={handleFinishPolygon}
        onPinTypeChange={onPinTypeChange}
        onClearShapes={onClearShapes}
        onClearPins={onClearPins}
        layerOptions={layerOptions}
        enabledLayers={advancedOptions.enabledLayers}
        onToggleLayer={onToggleLayer}
        baseLayers={BASE_LAYER_OPTIONS}
        baseLayerId={baseLayerId}
        onBaseLayerChange={(value: string) => setBaseLayerId(value)}
        polygonSummary={polygonSummary}
        hasActiveSession={!!location || !!result}
        onNewSession={onNewSession}
      />
    </div>
  );
}

interface MapToolbarProps {
  drawingMode: DrawingMode;
  selectedPinType: string;
  pinOptions: PinTypeOption[];
  pinsCount: number;
  onModeChange: (mode: DrawingMode) => void;
  onStartPolygon: () => void;
  onFinishPolygon: () => void;
  onPinTypeChange: (typeId: string) => void;
  onClearShapes: () => void;
  onClearPins: () => void;
  layerOptions: Array<{ key: LayerKey; label: string }>;
  enabledLayers: LayerKey[];
  onToggleLayer: (layer: LayerKey) => void;
  baseLayers: BaseLayerOption[];
  baseLayerId: string;
  onBaseLayerChange: (id: string) => void;
  onNewSession?: () => void;
  hasActiveSession: boolean;
  polygonSummary: {
    points: number;
    areaSqKm: number;
    perimeterKm: number;
  } | null;
}

function MapToolbar(props: MapToolbarProps) {
  const {
    drawingMode,
    selectedPinType,
    pinOptions,
    pinsCount,
    onModeChange,
    onStartPolygon,
    onFinishPolygon,
    onPinTypeChange,
    onClearShapes,
    onClearPins,
    layerOptions,
    enabledLayers,
    onToggleLayer,
    baseLayers,
    baseLayerId,
    onBaseLayerChange,
    onNewSession,
    hasActiveSession,
    polygonSummary,
  } = props;

  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);
  const layerMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isLayerMenuOpen) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (
        layerMenuRef.current &&
        event.target instanceof Node &&
        !layerMenuRef.current.contains(event.target)
      ) {
        setIsLayerMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isLayerMenuOpen]);

  const baseLayerOptions = useMemo(
    () =>
      baseLayers.map((layer) => ({
        value: layer.id,
        label: layer.label,
        description: layer.description,
      })),
    [baseLayers]
  );

  const pinTypeOptions = useMemo(
    () =>
      pinOptions.map((option) => ({
        value: option.id,
        label: option.label,
        description: option.description,
      })),
    [pinOptions]
  );

  const isPolygonActive = drawingMode === 'polygon';
  const isPinActive = drawingMode === 'pin';
  const hasPinOptions = pinTypeOptions.length > 0;
  const numberFormatter = useMemo(
    () => new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }),
    []
  );

  return (
    <div className="pointer-events-none absolute left-0 top-0 z-[1200] w-full">
      <div className="pointer-events-auto flex w-full flex-wrap items-center gap-3 border-b border-white/10 bg-[#1a1a1a] px-4 py-3 shadow-sm backdrop-blur-md">
        {onNewSession && hasActiveSession && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onNewSession}
          >
            New Session
          </Button>
        )}

        <div className="flex flex-wrap items-center gap-2">
          <div className="w-48 min-w-[160px]">
            <Select
              options={baseLayerOptions}
              value={baseLayerId}
              onChange={(value) => {
                if (typeof value === 'string') {
                  onBaseLayerChange(value);
                }
              }}
              isSearchable={false}
              placeholder="Map style"
            />
          </div>
        </div>

        <span className="hidden h-6 border-l border-white/10 lg:block" />

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant={isPolygonActive ? 'primary' : 'secondary'}
            size="sm"
            leftIcon={<Shapes className="h-4 w-4" />}
            onClick={() => {
              if (isPolygonActive) {
                onFinishPolygon();
              } else {
                onStartPolygon();
              }
            }}
          >
            {isPolygonActive ? 'Cancel drawing' : 'Draw area'}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            leftIcon={<Trash2 className="h-4 w-4" />}
            onClick={() => {
              onClearShapes();
              onModeChange('none');
            }}
          >
            Clear area
          </Button>
        </div>

        {isPolygonActive && (
          <div className="w-full border border-blue-500/30 bg-blue-900/20 px-3 py-2 text-xs text-blue-200 font-mono">
            <p className="font-bold uppercase tracking-wider text-blue-400">Drawing Mode Active</p>
            <p className="mt-0.5 text-blue-200/70">Click to add points. Double-click to finish.</p>
          </div>
        )}

        {polygonSummary && (
          <div className="flex flex-wrap items-center gap-3 border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-white font-mono">
            <span className="text-white/50 uppercase tracking-wider">Custom Area</span>
            <span>PTS: {polygonSummary.points}</span>
            <span>AREA: {numberFormatter.format(polygonSummary.areaSqKm)} km²</span>
            <span>PERIM: {numberFormatter.format(polygonSummary.perimeterKm)} km</span>
          </div>
        )}

        <span className="hidden h-6 border-l border-white/10 lg:block" />

        <div className="flex flex-wrap items-center gap-2">
          <div className="w-48 min-w-[160px]">
            <Select
              options={pinTypeOptions}
              value={selectedPinType}
              onChange={(value) => {
                if (typeof value === 'string') {
                  onPinTypeChange(value);
                }
              }}
              placeholder={hasPinOptions ? 'Choose pin type' : 'No pin types'}
              disabled={!hasPinOptions}
              isSearchable={false}
            />
          </div>
          <Button
            type="button"
            variant={isPinActive ? 'primary' : 'secondary'}
            size="sm"
            leftIcon={<MapPinIcon className="h-4 w-4" />}
            onClick={() => onModeChange(isPinActive ? 'none' : 'pin')}
            disabled={!hasPinOptions}
          >
            {isPinActive ? 'Stop placing pins' : 'Place pin'}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClearPins}
            disabled={pinsCount === 0}
          >
            Clear pins ({pinsCount})
          </Button>
        </div>

        <span className="hidden h-6 border-l border-white/10 lg:block" />

        <div className="relative" ref={layerMenuRef}>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            leftIcon={<Layers className="h-4 w-4" />}
            onClick={() => setIsLayerMenuOpen((prev) => !prev)}
            aria-expanded={isLayerMenuOpen}
            aria-haspopup="true"
          >
            Map layers
          </Button>
          {isLayerMenuOpen && (
            <div className="absolute right-0 top-full z-10 mt-2 w-60 rounded-md border border-emerald-900/10 bg-white p-3 shadow-lg">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-900/60">
                Visible layers
              </p>
              <ul className="max-h-56 space-y-2 overflow-y-auto text-sm text-emerald-900">
                {layerOptions.map((layer) => (
                  <li key={layer.key}>
                    <label className="flex cursor-pointer items-center justify-between gap-3">
                      <span className="truncate">{layer.label}</span>
                      <input
                        type="checkbox"
                        className="h-4 w-4 accent-emerald-600"
                        checked={enabledLayers.includes(layer.key)}
                        onChange={() => onToggleLayer(layer.key)}
                      />
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface FitBoundsEffectProps {
  location: LocationSelection | null;
}

function FitBoundsEffect({ location }: FitBoundsEffectProps) {
  const map = useMap();

  useEffect(() => {
    if (!location) return;

    if (
      location.type === 'custom' &&
      location.point &&
      (!location.polygon || location.polygon.length === 0)
    ) {
      return;
    }

    let bounds: LatLngBoundsExpression | null = null;

    if (location.type === 'park') {
      const { southWest, northEast } = location.bounds;
      bounds = [
        [southWest.lat, southWest.lng],
        [northEast.lat, northEast.lng],
      ];
    } else if (location.polygon?.length) {
      const latitudes = location.polygon.map((point) => point.lat);
      const longitudes = location.polygon.map((point) => point.lng);
      bounds = [
        [Math.min(...latitudes), Math.min(...longitudes)],
        [Math.max(...latitudes), Math.max(...longitudes)],
      ];
    } else if (location.point) {
      const { lat, lng } = location.point;
      bounds = [
        [lat - 0.01, lng - 0.01],
        [lat + 0.01, lng + 0.01],
      ];
    }

    if (bounds) {
      map.fitBounds(bounds, { padding: [32, 32] });
    }
  }, [location, map]);

  return null;
}
