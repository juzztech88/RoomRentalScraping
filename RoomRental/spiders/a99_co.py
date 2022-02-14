import scrapy

class A99CoSpider(scrapy.Spider):
    name = '99_co'
    allowed_domains = ['99.co']
    start_urls = ['https://99.co/singapore/rent/rooms/']

    def parse(self, response):
        listings = response.xpath('//*[@data-testid="searchListingItem"]')
        for listing in listings:
            properties = listing.xpath('.//p[@class="dniCg _2rhE- _1c-pJ"]/text()').extract()
            properties_dict = parse_room_property(properties)

            # selecting parsing description for property name
            description_sel = listing.xpath('.//a/text()')
            property_name = parse_description(description_sel)

            # selecting and parsing location cum condo information for address and property type (if condo)
            location_condo_sel = listing.xpath('.//span[@class="_3xhkj"]/text()')
            address, property_type_a = parse_location_condo(location_condo_sel)

            # selecting and parsing property type information
            property_type_sel = listing.xpath('.//p[@class="dniCg _1LPAx _2rhE- _1c-pJ"]/text()')
            property_type_b = parse_property_type(property_type_sel)

            # absorb property name into address
            if property_name != "" and address !="":
                address = property_name + ", " + address
            else:
                address = property_name + address

            # check consistency between the property type information extracted from location_condo_sel
            # and property_type_sel
            if property_type_a == "":
                property_type = property_type_b
            elif property_type_b == "":
                property_type = property_type_a
            else:
                if property_type_a != property_type_b:
                    property_type = 'Unknown'
                else:
                    property_type = property_type_a

            # select and parse train transportation information
            train_info_sel = listing.xpath('.//p[@class="dniCg _1RVkE _2rhE- _1c-pJ"]/text()')
            train_loc, train_dist = parse_train_info(train_info_sel)

            # select and prase room cost information
            room_cost_sel = listing.xpath('.//p[@class="_2sIc2 JlU_W _2rhE-"]/text()')
            room_cost = parse_cost(room_cost_sel)

            # compile the property information into a dictionary
            info_dict = {}
            info_dict['Address'] = address
            info_dict['Property_type'] = property_type
            info_dict['Montly_rental_SGD'] = room_cost
            info_dict['Train_location'] = train_loc
            info_dict['Train_distance_min'] = train_dist

            yield {**info_dict, **properties_dict}

        next_page_relurl = response.xpath('.//*[@class="next"]/a/@href').extract_first()
        yield scrapy.Request(response.urljoin(next_page_relurl), self.parse)

def parse_room_property(property_list):
    property_dict = {
        'Room_type' : "",
        'Dimension' : "",
        'Bathroom' : "",
        'Built-up' : 0,
    }
    for property in property_list:
        if 'room' in property:
            property_dict['Room_type'] = property.strip()
        elif 'sqft' in property:
            property = property.split(' sqft ')[0].replace(',', '')
            property_dict['Dimension_sqft'] = int(property)
        elif 'Bath' in property:
            property = property.split(' Bath')[0]
            property_dict['Bathroom'] = int(property)
        elif 'built-up' in property:
            property_dict['Built-up'] = 1

    return property_dict

def parse_description(sel):
    if sel:
        description = sel.extract_first()
        _ , property_name = description.split(' in ')
        return property_name.strip()
    else:
        return ""

def parse_location_condo(sel):
    if sel:
        location_condo = sel.extract_first()
        if 'Condo' in location_condo:
            address = location_condo.split('·')[0].strip()
            property_type = 'Condo'
        else:
            address = location_condo.strip()
            property_type = ""
    else:
        address = ""
        property_type = ""

    return address, property_type

def parse_property_type(sel):
    if sel:
        property_type = sel.extract_first().strip()
    else:
        property_type = ""
    return property_type

def parse_train_info(sel):
    if sel:
        train_info = sel.extract()
        train_loc, train_dist = [info.strip() for info in train_info]

        # convert distance to unit of minutes
        train_dist = int(train_dist.split(" ")[0])
    else:
        train_loc = ""
        train_dist = ""
    return train_loc, train_dist

def parse_cost(sel):
    if sel:
        room_cost = sel.extract_first().split('/mo')[0]
        room_cost = room_cost[1:]
        room_cost = int(room_cost.replace(',',''))
    else:
        room_cost = ""
    return room_cost
