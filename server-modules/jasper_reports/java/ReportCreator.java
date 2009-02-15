import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.util.JRXmlUtils;
import net.sf.jasperreports.engine.query.JRXPathQueryExecuterFactory;
import net.sf.jasperreports.engine.JRQuery;
import net.sf.jasperreports.view.JasperViewer;
import org.w3c.dom.Document;
import java.sql.*;
import java.util.*;
import java.io.FileInputStream;

public class ReportCreator {

	static String reportFile;
	static String xmlFile;
	static String outputFile;
	static String dsn;
	static String user;
	static String password;
	static String params;

	public static void createReport()
	{
		try {
			JasperReport report;
			JRQuery query;
			JasperPrint jasperPrint=null;
			String subreportDir;
			int index;
			
			report = (JasperReport) JRLoader.loadObject( reportFile );
			query = report.getQuery();
			
			Map parameters = parsedParameters();

			subreportDir = reportFile.substring( 0, reportFile.lastIndexOf('/') );
			index = reportFile.lastIndexOf('/');
			if ( index != -1 )
				parameters.put( "SUBREPORT_DIR", reportFile.substring( 0, index+1 ) );

			if( query.getLanguage().equalsIgnoreCase(  "XPATH")  ){
				JRXmlDataSource dataSource = new JRXmlDataSource( xmlFile, "/data/record" );
				dataSource.setDatePattern( "yyyy-MM-dd mm:hh:ss" );
				dataSource.setNumberPattern( "#######0.##" );
				dataSource.setLocale( Locale.ENGLISH );
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			} else if(  query.getLanguage().equalsIgnoreCase( "SQL")  ) {
				Connection con=null;
				try {
					con = getConnection();
					jasperPrint = JasperFillManager.fillReport( report, parameters, con );
				} catch( Exception e ){
					e.printStackTrace();
				}
			}
			JasperExportManager.exportReportToPdfFile( jasperPrint, outputFile );
		} catch (Exception e){
			e.printStackTrace();
			System.out.println( e.getMessage() );
		}
	}

	public static Connection getConnection() 
		throws java.lang.ClassNotFoundException, java.sql.SQLException
	{
		Connection connection;
		Class.forName("org.postgresql.Driver");

		connection = DriverManager.getConnection( dsn, user, password );
		connection.setAutoCommit(false);
		return connection;
	}

	public static HashMap parsedParameters(){
		HashMap parameters = new HashMap();
		System.out.println( "Params: " + params );
		String[] p = params.split(";");
		for( int j=0; j < p.length ; j++ ){
			System.out.println( p[j] );
			String[] map = p[j].split(":");
			if ( map.length == 2 ) 
				parameters.put( map[0] , map[1] );
		}
		System.out.println( parameters );
		return parameters;
	}

	public static void main( String[] args ) 
	{
		for( int i=0;i< args.length; i++ )
			System.out.println( "arguments:" + args[i]);

		HashMap parameters;

		if ( args.length < 7 ) {  
			System.out.println( "Seven arguments needed." );
			return;
		}

		reportFile = args[0];
		xmlFile = args[1];
		outputFile = args[2];
		dsn = args[3];
		user = args[4];
		password = args[5];
		params = args[6];
		createReport();
	}
}

