# inventory

Inventory system for electronics manufacturing. Base models are Parts -> Modules -> Devices, Demands, PartOrders -> Orders, Suppliers.

Devices consist of Modules which consist of Parts. Demands can be created from any of those three nad converted into Orders. Upon delivery, an order automatically increments stock count of its constituent parts; likewise Demands substract stock count upon fulfilment.

## Parts
<img width="1892" alt="Screen Shot 2022-11-06 at 12 30 21" src="https://user-images.githubusercontent.com/24959629/200168073-ce37a741-9166-4669-a07a-ebaf0a04338a.png">

## Module
<img width="1320" alt="Screen Shot 2022-11-06 at 12 29 52" src="https://user-images.githubusercontent.com/24959629/200168234-8f716bc0-62f5-4f4d-b018-c39c8d3cc56d.png">

## Device
<img width="1323" alt="Screen Shot 2022-11-06 at 12 29 41" src="https://user-images.githubusercontent.com/24959629/200168240-9cee2ccf-5444-425b-aa47-63da4aa1002e.png">

## Order
<img width="1322" alt="Screen Shot 2022-11-06 at 12 30 00" src="https://user-images.githubusercontent.com/24959629/200168245-f56588fc-05bb-4c3f-9f89-4c5177fd914d.png">
