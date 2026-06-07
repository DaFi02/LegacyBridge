import React, { useState, useEffect } from 'react';

interface Producto {
  codigo: string;
  nombre: string;
  precio: number;
  stock: number;
  minimo: number;
}

interface Transaccion {
  hora: string;
  producto: string;
  cantidad: number;
  monto: number;
}

const App = () => {
  const [currentSection, setCurrentSection] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [time, setTime] = useState(new Date());

  const productos: Producto[] = [
    { codigo: "P001", nombre: "Laptop HP ProBook", precio: 3200.00, stock: 15, minimo: 5 },
    { codigo: "P002", nombre: "Mouse Inalámbrico", precio: 45.00, stock: 230, minimo: 50 },
    { codigo: "P003", nombre: "Teclado Mecánico", precio: 189.00, stock: 3, minimo: 10 },
    { codigo: "P004", nombre: "Monitor 24 LED", precio: 890.00, stock: 28, minimo: 8 },
    { codigo: "P005", nombre: "Cable HDMI 2m", precio: 25.00, stock: 2, minimo: 20 },
    { codigo: "P006", nombre: "Webcam HD", precio: 120.00, stock: 45, minimo: 15 },
    { codigo: "P007", nombre: "Disco SSD 500GB", precio: 250.00, stock: 60, minimo: 10 },
    { codigo: "P008", nombre: "Memoria RAM 16GB", precio: 180.00, stock: 35, minimo: 12 }
  ];

  const transacciones: Transaccion[] = [
    { hora: "09:15", producto: "Mouse Inalámbrico", cantidad: 3, monto: 135.00 },
    { hora: "09:42", producto: "Cable HDMI 2m", cantidad: 5, monto: 125.00 },
    { hora: "10:05", producto: "Laptop HP ProBook", cantidad: 1, monto: 3200.00 },
    { hora: "10:30", producto: "Disco SSD 500GB", cantidad: 2, monto: 500.00 },
    { hora: "11:15", producto: "Webcam HD", cantidad: 4, monto: 480.00 },
    { hora: "11:50", producto: "Memoria RAM 16GB", cantidad: 3, monto: 540.00 }
  ];

  const totalIngresos = transacciones.reduce((acc, t) => acc + t.monto, 0);
  const alertas = productos.filter(p => p.stock <= p.minimo).length;

  useEffect(() => {
    const intervalId = setInterval(() => {
      setTime(new Date());
    }, 1000);
    return () => clearInterval(intervalId);
  }, []);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value.toLowerCase());
  };

  const filteredProductos = productos.filter(p => 
    p.codigo.toLowerCase().includes(searchTerm) || 
    p.nombre.toLowerCase().includes(searchTerm)
  );

  return (
    <div className="font-sans text-sm bg-gray-100 p-2.5">
      <div className="bg-blue-800 text-white p-2 flex justify-between">
        <span className="font-bold">&#9733; Panel de Control - Inventario Central</span>
        <span className="text-lg">{time.toLocaleTimeString()}</span>
      </div>

      <div className="flex mt-2.5">
        <div className="bg-gray-200 w-72 p-2.5 border-r border-gray-300">
          <b>Menú</b>
          <div className="mt-2.5">
            <a href="#" className="block p-1.5 text-blue-800 hover:bg-gray-300 border-b border-dotted border-gray-300" onClick={() => setCurrentSection('dashboard')}>&#9656; Dashboard</a>
            <a href="#" className="block p-1.5 text-blue-800 hover:bg-gray-300 border-b border-dotted border-gray-300" onClick={() => setCurrentSection('productos')}>&#9656; Productos</a>
            <a href="#" className="block p-1.5 text-blue-800 hover:bg-gray-300 border-b border-dotted border-gray-300" onClick={() => setCurrentSection('ventas')}>&#9656; Ventas</a>
            <a href="#" className="block p-1.5 text-blue-800 hover:bg-gray-300 border-b border-dotted border-gray-300" onClick={() => setCurrentSection('reportes')}>&#9656; Reportes</a>
          </div>
          <hr className="my-2.5" />
          <span className="text-xs text-gray-600">
            Usuario: admin<br />
            Sesión: activa
          </span>
        </div>

        <div className="p-2.5 flex-1">
          {currentSection === 'dashboard' && (
            <div>
              <h3 className="text-blue-800 mb-2.5">Resumen del Sistema</h3>
              <div className="flex flex-wrap">
                <div className="border border-gray-300 bg-white p-2.5 w-40 text-center mr-2.5 mb-2.5">
                  <div className="text-3xl font-bold text-blue-600">{productos.length}</div>
                  <div>Productos</div>
                </div>
                <div className="border border-gray-300 bg-white p-2.5 w-40 text-center mr-2.5 mb-2.5">
                  <div className="text-3xl font-bold text-blue-600">{transacciones.length}</div>
                  <div>Ventas Hoy</div>
                </div>
                <div className="border border-gray-300 bg-white p-2.5 w-40 text-center mr-2.5 mb-2.5">
                  <div className="text-3xl font-bold text-blue-600">S/. {totalIngresos.toFixed(0)}</div>
                  <div>Ingresos</div>
                </div>
                <div className="border border-gray-300 bg-white p-2.5 w-40 text-center mr-2.5 mb-2.5">
                  <div className="text-3xl font-bold text-blue-600">{alertas}</div>
                  <div>Alertas</div>
                </div>
              </div>

              <h4 className="mt-5">Últimas Transacciones</h4>
              <table className="w-full border-collapse mt-2.5">
                <thead>
                  <tr className="bg-blue-600 text-white">
                    <th className="p-1.5 text-left">Hora</th>
                    <th className="p-1.5 text-left">Producto</th>
                    <th className="p-1.5 text-left">Cantidad</th>
                    <th className="p-1.5 text-left">Monto</th>
                    <th className="p-1.5 text-left">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {transacciones.map((t, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-gray-100' : ''}>
                      <td className="border border-gray-300 p-1.5">{t.hora}</td>
                      <td className="border border-gray-300 p-1.5">{t.producto}</td>
                      <td className="border border-gray-300 p-1.5">{t.cantidad}</td>
                      <td className="border border-gray-300 p-1.5">S/. {t.monto.toFixed(2)}</td>
                      <td className="border border-gray-300 p-1.5 text-green-600 font-bold">OK</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {currentSection === 'productos' && (
            <div>
              <h3 className="text-blue-800 mb-2.5">Catálogo de Productos</h3>
              <input 
                type="text" 
                className="p-1 w-52 mr-2.5" 
                placeholder="Buscar..." 
                value={searchTerm} 
                onChange={handleSearch} 
              />
              <button className="bg-blue-600 text-white border border-gray-400 p-1 mr-2.5">Buscar</button>
              <button className="bg-blue-600 text-white border border-gray-400 p-1">Agregar Nuevo</button>
              <table className="w-full border-collapse mt-2.5">
                <thead>
                  <tr className="bg-blue-600 text-white">
                    <th className="p-1.5 text-left">Código</th>
                    <th className="p-1.5 text-left">Producto</th>
                    <th className="p-1.5 text-left">Precio</th>
                    <th className="p-1.5 text-left">Stock</th>
                    <th className="p-1.5 text-left">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProductos.map((p, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-gray-100' : ''}>
                      <td className="border border-gray-300 p-1.5">{p.codigo}</td>
                      <td className="border border-gray-300 p-1.5">{p.nombre}</td>
                      <td className="border border-gray-300 p-1.5">S/. {p.precio.toFixed(2)}</td>
                      <td className="border border-gray-300 p-1.5">{p.stock}</td>
                      <td className="border border-gray-300 p-1.5">
                        {p.stock <= p.minimo ? (
                          <span className="text-red-600 font-bold">BAJO</span>
                        ) : p.stock <= p.minimo * 2 ? (
                          <span className="text-orange-600 font-bold">MEDIO</span>
                        ) : (
                          <span className="text-green-600 font-bold">OK</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="text-center mt-5 p-2.5 bg-gray-200 text-xs text-gray-600">
        Sistema de Inventario Central v3.2 | &copy; 2005 TechSolutions SAC | Todos los derechos reservados
      </div>
    </div>
  );
};

export default App;