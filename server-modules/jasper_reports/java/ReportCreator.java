import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.util.JRXmlUtils;
import net.sf.jasperreports.engine.query.JRXPathQueryExecuterFactory;
import org.w3c.dom.Document;
import java.sql.*;
import java.util.*;
import java.io.FileInputStream;

public class ReportCreator {

	public static void createReport( String reportFile, String xmlFile, String reportOutput )
	{
		try {
			System.out.println( "Src: '" + reportFile + "'");
			System.out.println( "Xml: '" + xmlFile + "'");
			System.out.println( "Dst: '" + reportOutput + "'");
			JasperReport report;
			report = (JasperReport) JRLoader.loadObject( reportFile );

			Map parameters = new HashMap();
			//Document document = JRXmlUtils.parse( new FileInputStream(xmlFile) ); 
			//Document document = JRXmlUtils.parse( JRLoader.getLocationInputStream(xmlFile) ); 

			//parameters.put(JRXPathQueryExecuterFactory.PARAMETER_XML_DATA_DOCUMENT, document);
			//parameters.put(JRXPathQueryExecuterFactory.XML_DATE_PATTERN, "yyyy-MM-dd");
			//parameters.put(JRXPathQueryExecuterFactory.XML_NUMBER_PATTERN, "#,##0.##");
			//parameters.put(JRXPathQueryExecuterFactory.XML_LOCALE, Locale.ENGLISH);

			JRXmlDataSource dataSource = new JRXmlDataSource( xmlFile, "/data/record" );

			//parameters.put(JRXPathQueryExecuterFactory.PARAMETER_XML_DATA_DOCUMENT,document); 
			//JRXmlDataSource dataSource = new JRXmlDataSource(arrayInputStream,"partite") Thanks
			//dataSource.moveFirst();
			//System.out.println( "HOLA? " + dataSource.next() );
			//System.out.println( "HOLA? " + dataSource.next() );
			//parameters.put("Language", "ca");
			//parameters.put("Number", new Integer(25));

			// If XML:
			JasperPrint jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			//JasperFillManager.fillReportToFile( reportFile, parameters );
			System.out.println( "After: "  );
			// If JDBC:
			//JasperPrint jasperPrint = JasperFillManager.fillReport( report, parameters, getConnection() );

			JasperExportManager.exportReportToPdfFile( jasperPrint, reportOutput );
		} catch (Exception e){
			System.out.println( e.getMessage() );
		}
	}

	public static Connection getConnection() throws java.lang.ClassNotFoundException, java.sql.SQLException
	{
		Connection connection;
		Class.forName("org.postgresql.Driver");
		connection = DriverManager.getConnection("jdbc:postgresql://localhost:5432/database","user","password");
		return connection;
	}

	public static void main( String[] args ) 
	{
		if ( args.length == 3 )
			createReport( args[0], args[1], args[2] );
		else
			System.out.println( "Three arguments needed." );
	}
}

