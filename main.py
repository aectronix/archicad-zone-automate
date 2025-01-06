import argparse
import time
from archicad import ACConnection

start = time.time()
config = {
	'layers': {
		'single': 'S10 Single spaces (rooms)',								# layer name to filter zones (set to None in order to fetch every zone)
	},
	'props': {
		'layer': 'ModelView_LayerName',										# property for single zone layer's name
		'category': 'Zone_ZoneCategoryCode',								# property for zone category code
		'area': 'Zone_CalculatedArea',										# property for area measurement
		'area_m': 'Zone_MeasuredArea',										# property for area measurement
		# custom:
		'live': ['ZONES', 'Zone Living'],									# group name & property to define whether zone is live
		'tag': ['ZONES - Gross', 'Zone Tag'],								# group name & property for zone "tag" (used as unique ID)
		'area_gross': ['ZONES - Gross', 'Zone Area Gross'],					# group name & property of zone gross area field
		'area_m_gross': ['ZONES - Gross', 'Zone Area Gross (M)'],			# group name & property of zone gross area field
		'area_live': ['ZONES - Gross', 'Zone Area Live'],					# group name & property of zone live area field
		'area_m_live': ['ZONES - Gross', 'Zone Area Live (M)'],					# group name & property of zone live area field
		'update': ['ZONES - Gross', 'Zone Update'],							# group name & property to store the last refresh date
	},
	'round': 2																# rounding value, the number of digits after the point
}


def timer():
	return round(time.time() - start, 2)


class ZoneCommands():
	"""Collection of comands dedicated to operations with zones"""

	def __init__(self):

		cmd = argparse.ArgumentParser()
		cmd.add_argument('--port', type=int, default=None, required=False)
		arg = cmd.parse_args()

		self.conf = config
		self.acc = None

		self.connect()

	def connect(self):

		try:
			con = ACConnection.connect()
			if con.commands.IsAlive():
				navigator = con.commands.GetNavigatorItemTree(con.types.NavigatorTreeId('ProjectMap'))
				project = navigator.rootItem.children[0].navigatorItem.name if navigator else ""
				print(f'{timer()}: Connected to Archicad ' + str(con.commands.GetProductInfo()) + ' on port ' + str(con.port) + ' with file "' + project + '"')
				self.acc = con
		except Exception as e:
			print(f'{timer()}: No Archicad connection found! Check specified ports.\n')
			raise

	def cmd_area_update(self):
		"""
			Parses all specified zones, summarizes gross and live areas, writes it back to properties.
			Uses Zone Tag to "group" area data and allocate among the zones.
		"""

		# todo: filter by layer

		print(f'{timer()}: Retrieving all zones, extracting data...')
		zones = self.acc.commands.GetElementsByType('Zone')
		assert len(zones) > 0, f'{timer()} Could not find any suitable zone in the project!'

		try:
			tag_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['tag'][0], self.conf['props']['tag'][1])
			layer_propId = self.acc.utilities.GetBuiltInPropertyId(self.conf['props']['layer'])
			category_propId = self.acc.utilities.GetBuiltInPropertyId(self.conf['props']['category'])
			area_propId = self.acc.utilities.GetBuiltInPropertyId(self.conf['props']['area'])
			area_m_propId = self.acc.utilities.GetBuiltInPropertyId(self.conf['props']['area_m'])
			live_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['live'][0], self.conf['props']['live'][1])
		except Exception as e:
			print(f'{timer()}: Some custom properties have been missed!\n')
			raise			

		zones_prop = self.acc.commands.GetPropertyValuesOfElements(zones, [tag_propId, layer_propId, category_propId, area_propId, area_m_propId, live_propId])
		zones_data = {}

		# extract & store zone data
		print(f'{timer()}: Processing {len(zones)} items...')
		for zp in zones_prop:
			if zp.propertyValues[0].propertyValue.status != 'notAvailable' and self.conf['layers']['single'] and zp.propertyValues[1].propertyValue.value == self.conf['layers']['single']:
				idx = zones_prop.index(zp)
				# print('> Processing ' + str(idx+1) + '/' + str(len(zones)) + ' (' + str(zones[idx].elementId.guid) + ')...', end='\r')
				zone_tag = zp.propertyValues[0].propertyValue.value
				zone_area = round(zp.propertyValues[3].propertyValue.value, self.conf['round'])
				zone_area_m = round(zp.propertyValues[4].propertyValue.value, self.conf['round'])
				zone_live = zone_area if zp.propertyValues[5].propertyValue.value else 0
				zone_live_m = zone_area_m if zp.propertyValues[5].propertyValue.value else 0

				zones_data[zone_tag] = {
					'gross': zones_data.get(zone_tag, {}).get('gross', 0) + zone_area,
					'gross_m': zones_data.get(zone_tag, {}).get('gross_m', 0) + zone_area_m,
					'live': zones_data.get(zone_tag, {}).get('live', 0) + zone_live,
					'live_m': zones_data.get(zone_tag, {}).get('live', 0) + zone_live_m,
					'update': round(start)
				}

		print(f'{timer()}: Sending gross areas back to zones...')
		query = []
		gross_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['area_gross'][0], self.conf['props']['area_gross'][1]).guid
		gross_m_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['area_m_gross'][0], self.conf['props']['area_m_gross'][1]).guid
		live_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['area_live'][0], self.conf['props']['area_live'][1]).guid
		live_m_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['area_m_live'][0], self.conf['props']['area_m_live'][1]).guid
		update_propId = self.acc.utilities.GetUserDefinedPropertyId(self.conf['props']['update'][0], self.conf['props']['update'][1]).guid
		for zone in zones_prop:
			if zone.propertyValues[0].propertyValue.status != 'notAvailable' and zone.propertyValues[1].propertyValue.value == self.conf['layers']['single']:
				idx = zones_prop.index(zone)
				query += [
					{
		                "elementId": { "guid": zones[idx].elementId.guid },
		                "propertyId": { "guid": gross_propId },
		                "propertyValue": {
		                    "type": "area",
		                    "status": "normal",
		                    "value": round(zones_data[zone.propertyValues[0].propertyValue.value]['gross'], self.conf['round'])
		                }
		            },
					{
		                "elementId": { "guid": zones[idx].elementId.guid },
		                "propertyId": { "guid": gross_m_propId },
		                "propertyValue": {
		                    "type": "area",
		                    "status": "normal",
		                    "value": round(zones_data[zone.propertyValues[0].propertyValue.value]['gross_m'], self.conf['round'])
		                }
		            },
					{
		                "elementId": { "guid": zones[idx].elementId.guid },
		                "propertyId": { "guid": live_propId },
		                "propertyValue": {
		                    "type": "area",
		                    "status": "normal",
		                    "value": round(zones_data[zone.propertyValues[0].propertyValue.value]['live'], self.conf['round'])
		                }
		            },
					{
		                "elementId": { "guid": zones[idx].elementId.guid },
		                "propertyId": { "guid": live_m_propId },
		                "propertyValue": {
		                    "type": "area",
		                    "status": "normal",
		                    "value": round(zones_data[zone.propertyValues[0].propertyValue.value]['live_m'], self.conf['round'])
		                }
		            },
					{
		                "elementId": { "guid": zones[idx].elementId.guid },
		                "propertyId": { "guid": update_propId },
		                "propertyValue": {
		                    "type": "string",
		                    "status": "normal",
		                    "value": time.strftime("%d %b %Y %H:%M", time.localtime(time.time()))
		                }
		            }
				]

		self.acc.commands.SetPropertyValuesOfElements(query)

		print(f'{timer()}: Done in %s sec' % (round(time.time() - start, 2)))
	

# Run zone operations
if __name__ == '__main__':
	print(f'Please run the next scripts:\n\n>\t"area_update.py": to summarize zone areas')
