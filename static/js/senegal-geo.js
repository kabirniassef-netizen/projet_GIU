// Découpage administratif du Sénégal : région → département → communes.
// Les listes Région / Département / Commune des formulaires de signalement
// affichent tout par défaut et se filtrent mutuellement lors d'un choix.
const SENEGAL_GEO = {
  'Dakar': {
    'Dakar': 'Dakar-Plateau|Gorée|Médina|Gueule Tapée-Fass-Colobane|Fann-Point E-Amitié|Biscuiterie|Dieuppeul-Derklé|HLM|Hann Bel-Air|Sicap-Liberté|Grand Dakar|Grand Yoff|Mermoz-Sacré-Cœur|Ouakam|Ngor|Yoff|Parcelles Assainies|Cambérène|Patte d’Oie',
    'Guédiawaye': 'Golf Sud|Sam Notaire|Ndiarème Limamoulaye|Wakhinane Nimzatt|Médina Gounass',
    'Keur Massar': 'Keur Massar Nord|Keur Massar Sud|Malika|Yeumbeul Nord|Yeumbeul Sud|Jaxaay-Parcelles-Niakoul Rap',
    'Pikine': 'Pikine Est|Pikine Ouest|Pikine Nord|Dalifort|Djidah Thiaroye Kao|Guinaw Rail Nord|Guinaw Rail Sud|Thiaroye Gare|Thiaroye-sur-Mer|Tivaouane Diacksao|Diamaguène Sicap Mbao|Mbao',
    'Rufisque': 'Rufisque Est|Rufisque Nord|Rufisque Ouest|Bargny|Sébikotane|Diamniadio|Sendou|Sangalkam|Bambilor|Yène|Tivaouane Peulh-Niaga',
  },
  'Diourbel': {
    'Bambey': 'Bambey|Baba Garage|Dangalma|Dinguiraye|Gawane|Keur Samba Kane|Lambaye|Ndondol|Ngogom|Ngoye|Réfane|Thiakhar',
    'Diourbel': 'Diourbel|Dankh Sène|Gadé Escale|Keur Ngalgou|Ndindy|Ndoulo|Ngohé|Patar|Taïba Moutoupha|Tocky Gare|Touré Mbonde',
    'Mbacké': 'Mbacké|Touba Mosquée|Dalla Ngabou|Darou Nahim|Darou Salam Typ|Dendeye Gouyegui|Kaël|Madina|Missirah|Ndioumane|Nghaye|Sadio|Taïba Thiékène|Taïf|Touba Fall',
  },
  'Fatick': {
    'Fatick': 'Fatick|Diakhao|Diaoulé|Diarrère|Dioffior|Diouroup|Djilasse|Fimela|Loul Sessène|Mbéllacadiao|Ndiob|Niakhar|Ngayokhème|Palmarin Facao|Patar|Tattaguine|Thiaré Ndialgui',
    'Foundiougne': 'Foundiougne|Sokone|Karang Poste|Passy|Soum|Bassoul|Diagane Barka|Dionewar|Diossong|Djilor|Djirnda|Keur Saloum Diané|Keur Samba Guèye|Mbam|Niassène|Niodior|Nioro Alassane Tall|Toubacouta',
    'Gossas': 'Gossas|Colobane|Mbar|Ndiène Lagane|Ouadiour|Patar Lia',
  },
  'Kaffrine': {
    'Birkelane': 'Birkelane|Diamal|Keur Mboucki|Mabo|Mbeuleup|Ndiognick|Ségré-Gatta|Touba Mbella',
    'Kaffrine': 'Kaffrine|Nganda|Boulel|Diamagadio|Diokoul Mbelbouck|Gniby|Kahi|Kathiote|Médinatoul Salam 2',
    'Koungheul': 'Koungheul|Fass Thiékène|Gainth Pathé|Ida Mouride|Lour Escale|Maka Yop|Missirah Wadène|Ribot Escale|Saly Escale',
    'Malem Hodar': 'Malem Hodar|Darou Minam 2|Dianké Souf|Khelcom|Ndiobène Samba Lamo|Ndioum Ngainth|Sagna',
  },
  'Kaolack': {
    'Guinguinéo': 'Guinguinéo|Fass|Mboss|Dara Mboss|Gagnick|Khelcom-Birane|Mbadakhoune|Ndiago|Ngathie Naoudé|Nguélou|Ourour|Panal Wolof',
    'Kaolack': 'Kaolack|Kahone|Ndoffane|Gandiaye|Sibassor|Dya|Keur Baka|Keur Socé|Latmingué|Ndiaffate|Ndiebel|Ndiédieng|Thiaré|Thiomby',
    'Nioro du Rip': 'Nioro du Rip|Keur Madiabel|Dabaly|Darou Salam|Gainthe Kaye|Kayemor|Keur Maba Diakhou|Keur Madongo|Médina Sabakh|Ndramé Escale|Ngayène|Paoskoto|Porokhane|Taïba Niassène|Wack Ngouna',
  },
  'Kédougou': {
    'Kédougou': 'Kédougou|Bandafassi|Dimboli|Dindéfelo|Fongolimbi|Ninéfécha|Tomboronkoto',
    'Salémata': 'Salémata|Dakatéli|Dar Salam|Ethiolo|Kévoye|Oubadji',
    'Saraya': 'Saraya|Bembou|Khossanto|Médina Baffé|Missirah Sirimana|Sabodala',
  },
  'Kolda': {
    'Kolda': 'Kolda|Dabo|Salikégné|Saré Yoba Diéga|Bagadadji|Coumbacara|Dialambéré|Dioulacolon|Guiro Yéro Bocar|Mampatim|Médina Chérif|Médina El Hadj|Saré Bidji|Tankanto Escale|Thiétty',
    'Médina Yoro Foulah': 'Médina Yoro Foulah|Pata|Badion|Bignarabé|Bourouco|Dinguiraye|Fafacourou|Kéréwane|Koulinto|Ndorna|Niaming',
    'Vélingara': 'Vélingara|Diaobé-Kabendou|Kounkané|Bonconto|Kandia|Kandiaye|Linkering|Médina Gounass|Némataba|Pakour|Paroumba|Saré Coly Sallé|Sinthiang Koundara|Ouassadou',
  },
  'Louga': {
    'Kébémer': 'Kébémer|Guéoul|Ndande|Bandègne Ouolof|Darou Marnane|Darou Mousty|Diokoul Diawrigne|Kab Gaye|Kanène Ndiob|Loro|Mbacké Cajor|Mbadiane|Ndoyène|Ngourane|Sagatta Gueth|Sam Yabal|Thieppe|Thiolom Fall|Touba Mérina',
    'Linguère': 'Linguère|Dahra|Mbeuleukhé|Affé Djoloff|Barkédji|Boulal|Dealy|Dodji|Gassane|Kamb|Labgar|Mboula|Ouarkhokh|Sagatta Djoloff|Tessékéré Forage|Thiamène Pass|Thiargny|Thiel|Yang-Yang',
    'Louga': 'Louga|Coki|Gande|Guet Ardo|Kéle Guèye|Keur Momar Sarr|Léona|Mbédiène|Ndiagne|Ngueune Sarr|Nguer Malal|Nguidile|Niomré|Pété Ouarack|Sakal|Syer|Thiamène Cayor',
  },
  'Matam': {
    'Kanel': 'Kanel|Waoundé|Semmé|Dembancané|Hamady Ounaré|Odobéré|Ouro Sidy|Aouré|Bokiladji|Ndendory|Orkadiéré|Sinthiou Bamambé-Banadji',
    'Matam': 'Matam|Ourossogui|Thilogne|Nguidjilone|Agnam Civol|Bokidiawé|Dabia|Nabadji Civol|Ogo|Oréfondé',
    'Ranérou Ferlo': 'Ranérou|Lougré Thiolly|Oudalaye|Vélingara Ferlo',
  },
  'Saint-Louis': {
    'Dagana': 'Dagana|Richard-Toll|Rosso-Sénégal|Ross Béthio|Gaé|Ndombo Alarar|Bokhol|Diama|Gnith|Mbane|Ronkh',
    'Podor': 'Podor|Ndioum|Golléré|Méri|Aéré Lao|Démette|Galoya Toucouleur|Guédé Chantier|Mboumba|Pété|Walaldé|Bodé Lao|Boké Dialloubé|Dodel|Doumga Lao|Fanaye|Gamadji Saré|Guédé Village|Mbolo Birane|Médina Ndiathbé|Ndiayène Pendao|Ndiandane',
    'Saint-Louis': 'Saint-Louis|Mpal|Fass Ngom|Gandon|Ndiébène Gandiole',
  },
  'Sédhiou': {
    'Bounkiling': 'Bounkiling|Madina Wandifa|Ndiamacouta|Boghal|Bona|Diacounda|Diambati|Diaroumé|Djinany|Faoune|Inor|Kandion Mangana|Ndiamalathiel|Tankon',
    'Goudomp': 'Goudomp|Samine|Tanaff|Baghère|Diattacounda|Djibanar|Kaour|Karantaba|Kolibantang|Mangaroungou Santo|Niagha|Simbandi Balante|Simbandi Brassou|Yarang Balante',
    'Sédhiou': 'Sédhiou|Diannah Malary|Marsassoum|Bambali|Bémet Bidjini|Diannah Ba|Diendé|Djibabouya|Djiredji|Koussy|Oudoucar|Sakar|Sama Kanta Peulh',
  },
  'Tambacounda': {
    'Bakel': 'Bakel|Diawara|Kidira|Ballou|Bélé|Gabou|Gathiary|Madina Foulbé|Moudéry|Sadatou|Sinthiou Fissa|Toumboura',
    'Goudiry': 'Goudiry|Kothiary|Bala|Bani Israël|Boutoucoufara|Boynguel Bamba|Dianké Makha|Dougué|Koar|Komoti|Koulor|Sinthiou Bocar Aly|Sinthiou Mamadou Boubou',
    'Koumpentoum': 'Koumpentoum|Malème Niani|Bamba Thialène|Kahène|Kouthia Gaydi|Kouthiaba Wolof|Mereto|Ndame|Pass Koto|Payar',
    'Tambacounda': 'Tambacounda|Dialacoto|Koussanar|Makacolibantang|Missirah|Ndoga Babacar|Niani Toucouleur|Sinthiou Malème',
  },
  'Thiès': {
    'Mbour': 'Mbour|Joal-Fadiouth|Saly Portudal|Ngaparou|Somone|Popenguine-Ndayane|Nguékhokh|Thiadiaye|Diass|Fissel|Malicounda|Ndiaganiao|Nguéniène|Sandiara|Sessène|Sindia',
    'Thiès': 'Thiès Est|Thiès Nord|Thiès Ouest|Kayar|Khombole|Pout|Diender Guedj|Fandène|Keur Moussa|Ndiéyène Sirakh|Ngoundiane|Notto Diobass|Tassette|Thiénaba|Touba Toul',
    'Tivaouane': 'Tivaouane|Mékhé|Mboro|Chérif Lô|Darou Khoudoss|Koul|Mbayène|Méouane|Merina Dakhar|Mont-Rolland|Ngandiouf|Niakhène|Notto Gouye Diama|Pambal|Pékesse|Pire Goureye|Taïba Ndiaye|Thilmakha',
  },
  'Ziguinchor': {
    'Bignona': 'Bignona|Thionck Essyl|Diouloulou|Affiniam|Balinghore|Coubalan|Diégoune|Djibidione|Djinaky|Kafountine|Kartiack|Kataba 1|Mangagoulack|Mlomp|Niamone|Oulampane|Ouonck|Sindian|Suelle|Tendouck|Tenghory',
    'Oussouye': 'Oussouye|Diembéring|Mlomp|Oukout|Santhiaba Manjacque',
    'Ziguinchor': 'Ziguinchor|Adéane|Boutoupa-Camaracounda|Enampore|Niaguis|Nyassia',
  },
};

const SenegalGeo = (() => {
  const collator = new Intl.Collator('fr');
  const sorted = list => [...list].sort(collator.compare);
  const regions = sorted(Object.keys(SENEGAL_GEO));
  const departments = region => sorted(Object.keys(SENEGAL_GEO[region] || {}));
  const communes = (region, department) => sorted(((SENEGAL_GEO[region] || {})[department] || '').split('|').filter(Boolean));

  function option(value, label, data = {}) {
    const node = new Option(label || value, value);
    Object.assign(node.dataset, data);
    return node;
  }

  function fill(select, placeholder, groups, keep) {
    select.replaceChildren(option('', placeholder));
    groups.forEach(({ label, items }) => {
      const parent = label ? document.createElement('optgroup') : select;
      if (label) { parent.label = label; select.appendChild(parent); }
      items.forEach(item => parent.appendChild(option(item.value, item.value, item.data)));
    });
    // Conserve une valeur existante (ex. ancienne saisie libre) si elle est toujours pertinente.
    if (keep && ![...select.options].some(item => item.value === keep)) select.appendChild(option(keep));
    select.value = keep || '';
  }

  function bind(regionSelect, departmentSelect, communeSelect) {
    if (!regionSelect || !departmentSelect || !communeSelect) return;

    function renderRegions() {
      fill(regionSelect, 'Choisir une région', [{ items: regions.map(value => ({ value })) }], regionSelect.value);
    }

    function renderDepartments() {
      const region = regionSelect.value;
      const scope = SENEGAL_GEO[region] ? [region] : regions;
      const keep = scope.some(item => departments(item).includes(departmentSelect.value)) ? departmentSelect.value : '';
      fill(departmentSelect, 'Choisir un département', scope.map(item => ({
        label: scope.length > 1 ? `Région de ${item}` : '',
        items: departments(item).map(value => ({ value, data: { region: item } })),
      })), keep);
    }

    function renderCommunes() {
      const region = regionSelect.value;
      const department = departmentSelect.value;
      const pairs = regions
        .filter(item => !SENEGAL_GEO[region] || item === region)
        .flatMap(item => departments(item).map(dept => [item, dept]))
        .filter(([, dept]) => !department || dept === department);
      const current = communeSelect.selectedOptions[0];
      const stillValid = current && current.value && pairs.some(([item, dept]) => item === current.dataset.region && dept === current.dataset.department);
      const keep = stillValid ? current.value : '';
      fill(communeSelect, 'Choisir une commune', pairs.map(([item, dept]) => ({
        label: pairs.length > 1 ? `${dept} (${item})` : '',
        items: communes(item, dept).map(value => ({ value, data: { region: item, department: dept } })),
      })), keep);
      if (keep) {
        const match = [...communeSelect.options].find(item => item.value === keep && item.dataset.department === current.dataset.department);
        if (match) match.selected = true;
      }
    }

    regionSelect.addEventListener('change', () => { renderDepartments(); renderCommunes(); });
    departmentSelect.addEventListener('change', () => {
      const chosen = departmentSelect.selectedOptions[0];
      if (chosen && chosen.dataset.region) regionSelect.value = chosen.dataset.region;
      renderDepartments();
      renderCommunes();
    });
    communeSelect.addEventListener('change', () => {
      const chosen = communeSelect.selectedOptions[0];
      if (!chosen || !chosen.dataset.department) return;
      regionSelect.value = chosen.dataset.region;
      departmentSelect.value = chosen.dataset.department;
      renderDepartments();
      renderCommunes();
      const match = [...communeSelect.options].find(item => item.value === chosen.value && item.dataset.department === chosen.dataset.department);
      if (match) match.selected = true;
    });

    function renderAll() { renderRegions(); renderDepartments(); renderCommunes(); }
    // Après form.reset(), le navigateur remet les listes à zéro : on les reconstruit complètes.
    const form = regionSelect.form;
    if (form) form.addEventListener('reset', () => setTimeout(() => {
      regionSelect.value = ''; departmentSelect.value = ''; communeSelect.value = '';
      renderAll();
    }));
    renderAll();
  }

  return { bind, regions, departments, communes };
})();

document.addEventListener('DOMContentLoaded', () => {
  SenegalGeo.bind(
    document.getElementById('incidentRegion'),
    document.getElementById('incidentDepartment'),
    document.getElementById('incidentCommune'),
  );
});
