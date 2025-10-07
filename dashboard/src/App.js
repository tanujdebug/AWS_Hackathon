import React, { useState, useEffect } from 'react';
import { Layout, Card, Row, Col, Statistic, Alert, Spin } from 'antd';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const { Header, Content, Sider } = Layout;

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dronePositions, setDronePositions] = useState([]);
  const [victimPositions, setVictimPositions] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/dashboard/data`);
      const data = response.data;
      
      setDashboardData(data);
      setSystemStatus(data.system_status);
      
      // Process drone positions from telemetry
      const dronePos = data.telemetry.map(t => ({
        id: t.drone_id,
        lat: t.position.lat,
        lon: t.position.lon,
        battery: t.battery_pct,
        status: t.status,
        timestamp: t.timestamp_utc
      }));
      setDronePositions(dronePos);
      
      // Process victim positions
      const victimPos = data.victims.map(v => ({
        id: v.id,
        lat: v.lat,
        lon: v.lon,
        survival_likelihood: v.survival_likelihood,
        injury_level: v.injury_level,
        priority_score: v.priority_score
      }));
      setVictimPositions(victimPos);
      
      // Process routes
      setRoutes(data.routes);
      
      setLoading(false);
      setError(null);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getInjuryColor = (injuryLevel) => {
    const colors = {
      'none': '#52c41a',
      'minor': '#faad14',
      'severe': '#fa8c16',
      'unconscious': '#f5222d'
    };
    return colors[injuryLevel] || '#666';
  };

  const getSurvivalColor = (likelihood) => {
    if (likelihood > 0.8) return '#52c41a';
    if (likelihood > 0.6) return '#faad14';
    if (likelihood > 0.4) return '#fa8c16';
    return '#f5222d';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description={`Failed to load dashboard data: ${error}`}
        type="error"
        showIcon
      />
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', color: 'white', textAlign: 'center' }}>
        <h1 style={{ color: 'white', margin: 0 }}>Drone Swarm Earthquake Rescue System</h1>
      </Header>
      
      <Layout>
        <Sider width={300} style={{ background: '#f0f2f5', padding: '16px' }}>
          <Card title="System Status" style={{ marginBottom: 16 }}>
            <Statistic
              title="Active Drones"
              value={systemStatus?.active_drones || 0}
              valueStyle={{ color: '#3f8600' }}
            />
            <Statistic
              title="Total Victims"
              value={systemStatus?.total_victims || 0}
              valueStyle={{ color: '#cf1322' }}
            />
            <Statistic
              title="Available Responders"
              value={systemStatus?.available_responders || 0}
              valueStyle={{ color: '#1890ff' }}
            />
            <Statistic
              title="Avg Survival Likelihood"
              value={systemStatus?.average_survival_likelihood || 0}
              precision={3}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>

          <Card title="Victim Priority" style={{ marginBottom: 16 }}>
            {victimPositions.slice(0, 5).map(victim => (
              <div key={victim.id} style={{ marginBottom: 8, padding: 8, background: '#f9f9f9', borderRadius: 4 }}>
                <div style={{ fontWeight: 'bold' }}>Victim {victim.id}</div>
                <div style={{ color: getSurvivalColor(victim.survival_likelihood) }}>
                  Survival: {(victim.survival_likelihood * 100).toFixed(1)}%
                </div>
                <div style={{ color: getInjuryColor(victim.injury_level) }}>
                  Injury: {victim.injury_level}
                </div>
              </div>
            ))}
          </Card>

          <Card title="Active Routes">
            {routes.map(route => (
              <div key={route.responder_id} style={{ marginBottom: 8, padding: 8, background: '#f9f9f9', borderRadius: 4 }}>
                <div style={{ fontWeight: 'bold' }}>Responder {route.responder_id}</div>
                <div>Distance: {(route.total_distance / 1000).toFixed(1)} km</div>
                <div>Time: {route.estimated_time.toFixed(1)} hours</div>
                <div>Victims: {route.victims_served.length}</div>
              </div>
            ))}
          </Card>
        </Sider>

        <Content style={{ padding: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Real-time Map" style={{ height: '600px' }}>
                <MapContainer
                  center={[34.0522, -118.2437]}
                  zoom={15}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  
                  {/* Drone markers */}
                  {dronePositions.map(drone => (
                    <Marker
                      key={drone.id}
                      position={[drone.lat, drone.lon]}
                    >
                      <Popup>
                        <div>
                          <strong>Drone {drone.id}</strong><br />
                          Battery: {drone.battery}%<br />
                          Status: {drone.status}<br />
                          Time: {new Date(drone.timestamp).toLocaleTimeString()}
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  
                  {/* Victim markers */}
                  {victimPositions.map(victim => (
                    <Marker
                      key={victim.id}
                      position={[victim.lat, victim.lon]}
                    >
                      <Popup>
                        <div>
                          <strong>Victim {victim.id}</strong><br />
                          Survival: {(victim.survival_likelihood * 100).toFixed(1)}%<br />
                          Injury: {victim.injury_level}<br />
                          Priority: {victim.priority_score.toFixed(1)}
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  
                  {/* Route lines */}
                  {routes.map(route => {
                    const routeCoords = route.route.map(victimId => {
                      const victim = victimPositions.find(v => v.id === victimId);
                      return victim ? [victim.lat, victim.lon] : null;
                    }).filter(coord => coord !== null);
                    
                    if (routeCoords.length > 0) {
                      return (
                        <Polyline
                          key={route.responder_id}
                          positions={routeCoords}
                          color="blue"
                          weight={3}
                        />
                      );
                    }
                    return null;
                  })}
                </MapContainer>
              </Card>
            </Col>
          </Row>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
